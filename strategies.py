
import logging
import time

from models import Contract, Candle
import typing

logger = logging.getLogger()

TF_EQUIV = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600, '4h': 14400}


class Strategy:
    def __init__(self, client, contract: Contract, exchange: str, time_frame: str, balance_percentage: float,
                 take_profit: float, stop_loss: float):
        self.client = client
        self.contract = contract
        self.exchange = exchange
        self.time_frame = time_frame
        self.tf_equiv = TF_EQUIV[time_frame] * 1000
        self.balance_percentage = balance_percentage
        self.take_profit = take_profit
        self.stop_loss = stop_loss

        self.open_position = False
        self.candles: typing.List[Candle] = []

    # there are three cases here. The incoming aggregated market information would (represented by a trade info)
    # 1- update the current candle (the last index in this list self.candles)
    # 2- be the first trade in the new candle which means we need to add a new candle to this list self.candles
    # 3- be the first trade in the new candle but there were missing candles between the last one
    #    we have recorded in this list self.candles and the new candle, this case can happen with contracts that dont
    #    have a lot of volume. Sometimes  there is no trade during a few mins. Which means we need to add the missing
    #    candles to the self.candles

    def parse_trades_to_update_current_candle(self, price: float, size: float, timestamp: int) -> str:

        timestamp_difference = int (time.time() * 1000) - timestamp
        if timestamp_difference >= 1000:
            logger.warning(f'%s %s: %s milliseconds of difference between the system current time and trade time '
                           f'(timed by the exchange)', self.exchange, self.contract.symbol, timestamp_difference)

        last_candle: Candle = self.candles[-1]

        # 1- first case: current candle
        if timestamp < last_candle.open_time + self.tf_equiv:

            last_candle.close = price
            last_candle.volume = last_candle.volume + size

            if price > last_candle.high:
                last_candle.high = price
            elif price < last_candle.low:
                last_candle.low = price
            logger.info(f'Last candle updated in the list of candles for %s with timeframe %s', self.contract.symbol,
                        self.time_frame)

            return 'same_candle'


        # 3- third case: missing candles
        elif timestamp >= last_candle.open_time + 2 * self.tf_equiv:
            missing_candles_count = int((timestamp - last_candle.open_time) / self.tf_equiv) - 1

            for i in range(missing_candles_count):
                new_candle_open_time = last_candle.open_time + self.tf_equiv
                new_candle_close_time = last_candle.open_time + 2 * self.tf_equiv
                candle_data = {
                    'open_time': new_candle_open_time,
                    'open': last_candle.close,
                    'high': last_candle.close,
                    'low': last_candle.close,
                    'close': last_candle.close,
                    'volume': 0,
                    'close_time': new_candle_close_time
                }
                new_candle = Candle(candle_data)
                self.candles.append(new_candle)
                last_candle = new_candle
            logger.info(f'%s missing candles added to the list of candles for %s with timeframe %s',
                        missing_candles_count,
                        self.contract.symbol,
                        self.time_frame)
            return 'new_candle'


        # 2- second case: new candle
        elif timestamp >= last_candle.open_time + self.tf_equiv:
            new_candle_open_time = last_candle.open_time + self.tf_equiv
            new_candle_close_time = last_candle.open_time + 2 * self.tf_equiv
            candle_data = {
                'open_time': new_candle_open_time,
                'open': price,
                'high': price,
                'low': price,
                'close': price,
                'volume': size,
                'close_time': new_candle_close_time
            }
            new_candle = Candle(candle_data)
            self.candles.append(new_candle)
            logger.info(f'New candle added to the list of candles for %s with timeframe %s', self.contract.symbol,
                        self.time_frame)

            return 'new_candle'

    # we can place an order without a bid and ask price by placing a market order
    # however if we need the bid and ask price we can pass them as arguments from the connector
    def open_position_with_market_order(self, signal_result: int):
        pass

    def open_position_with_limit_order(self, signal_result: int, bid: float, ask: float):
        pass


class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, time_frame: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, time_frame, balance_percentage, take_profit, stop_loss)
        self._ema_fast = other_params['ema_fast']
        self._ema_slow = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']
        logger.info(f'Activated technical strategy for {contract.symbol}')

    def check_trade(self, tick_type: str):
        pass


class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, time_frame: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, time_frame, balance_percentage, take_profit, stop_loss)
        self._min_volume = other_params['min_volume']
        logger.info(f'Activated breakout strategy for {contract.symbol}')

    # to determine if we need to enter a long trade or short trade or do nothing
    def _check_signal(self) -> int:
        if self.candles[-1].close > self.candles[-2].high and self.candles[-1].volume > self._min_volume:
            return 1
        elif self.candles[-1].close < self.candles[-2].low and self.candles[-1].volume > self._min_volume:
            return -1
        else:
            return 0

    def _check_inside_bar_pattern(self):
        if self.candles[-2].high < self.candles[-3].high and self.candles[-2].low > self.candles[-3].low:
            if self.candles[-1].close > self.candles[-3].high:
                # Upside breakout
                logger.info(f"Upside breakout pattern circumstances have been met")
            elif self.candles[-1].close < self.candles[-3].low:
                # Downside breakout
                logger.info(f"Downside breakout pattern circumstances have been met")

    def check_trade(self, tick_type: str):
        if not self.open_position:
            signal_result = self._check_signal()
            if signal_result in [1, -1]:
                self.open_position_with_market_order(signal_result)


