
import logging
import time
from connectors.binance_enums import *
from enums import *

from threading import Timer

from models import *
import typing

# due to circular import issue
if typing.TYPE_CHECKING:
    from connectors.binance_futures import BinanceFuturesClient

logger = logging.getLogger()

TF_EQUIV = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800, '1h': 3600, '4h': 14400}


class Strategy:
    def __init__(self, client: typing.Union["BinanceFuturesClient"], contract: Contract, exchange: str, time_frame: str,
                 balance_percentage: float, take_profit: float, stop_loss: float,strategy_name : str):

        self.client = client
        self.contract = contract
        self.exchange = exchange
        self.time_frame = time_frame
        self.tf_equiv = TF_EQUIV[time_frame] * 1000
        self.balance_percentage = balance_percentage
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.strategy_name = strategy_name

        self.ongoing_position = False
        self.candles: typing.List[Candle] = []
        self.trades: typing.List[Trade] = []

        self.logs = list()

    def _add_log(self, message: str):
        logger.info(message)
        self.logs.append({'message': message, 'displayed': False})

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
    def open_position_with_market_order(self, signal_result: PositionSide):
        trade_size = self.client.get_trade_size(self.contract, self.candles[-1].close, self.balance_percentage)
        if trade_size is None:
            return
        self._add_log(f'{signal_result.name} signal triggered on {self.contract.symbol} with {self.time_frame} time frame '
                     f'and trade size: {trade_size}')

        side = OrderSide.BUY if signal_result is PositionSide.LONG else OrderSide.SELL
        order_status = self.client.place_order(contract=self.contract,
                                                   side=side,
                                                   quantity=trade_size,
                                                   order_type=OrderType.MARKET)
        self._add_log(f'{side.name} order placed on {self.exchange} | Status: {order_status.status}')
        self.ongoing_position = True

        average_filled_price = None
        if order_status.status is OrderStatus.FILLED:
            average_filled_price = order_status.avg_price
        elif order_status.status is OrderStatus.PARTIALLY_FILLED or OrderStatus.NEW:
            timer = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
            timer.start()

        new_trade = Trade(time=int(time.time() * 1000), contract=self.contract, strategy=self.strategy_name, side=side,
                          entry_price=average_filled_price, quantity=trade_size, entry_id=order_status.order_id,
                          pnl=0, status=TradeStatus.OPEN)
        self.trades.append(new_trade)









    def open_position_with_limit_order(self, signal_result: int, bid: float, ask: float):
        pass

    def _check_order_status(self, order_id: int):
        order_status = self.client.get_order_status(self.contract, order_id)
        if order_status is not None and order_id == order_status.order_id:
            logger.info(f'{self.exchange} order Status: {order_status.status.name}')
            if order_status.status is OrderStatus.FILLED:
                for trade in self.trades:
                    if trade.entry_id == order_status.order_id:
                        trade.entry_price = order_status.avg_price
                        break
                return
        timer = Timer(2.0, lambda: self._check_order_status(order_id))
        timer.start()

class TechnicalStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, time_frame: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, time_frame, balance_percentage, take_profit, stop_loss, 'Technical')
        self._ema_fast = other_params['ema_fast']
        self._ema_slow = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']
        logger.info(f'Activated technical strategy for {contract.symbol}')

    def check_trade(self, tick_type: str):
        pass


class BreakoutStrategy(Strategy):
    def __init__(self, client, contract: Contract, exchange: str, time_frame: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        super().__init__(client, contract, exchange, time_frame, balance_percentage, take_profit, stop_loss, 'Breakout')
        self._min_volume = other_params['min_volume']
        logger.info(f'Activated breakout strategy for {contract.symbol}')

    # to determine if we need to enter a long trade or short trade or do nothing
    def _check_signal(self) -> typing.Union[PositionSide, None]:
        if self.candles[-1].close > self.candles[-2].high and self.candles[-1].volume > self._min_volume:
            #Long trade
            return PositionSide.LONG
        elif self.candles[-1].close < self.candles[-2].low and self.candles[-1].volume > self._min_volume:
            #Short trade
            return PositionSide.SHORT
        else:
            return None

    def _check_inside_bar_pattern(self):
        if self.candles[-2].high < self.candles[-3].high and self.candles[-2].low > self.candles[-3].low:
            if self.candles[-1].close > self.candles[-3].high:
                # Upside breakout
                logger.info(f"Upside breakout pattern circumstances have been met")
            elif self.candles[-1].close < self.candles[-3].low:
                # Downside breakout
                logger.info(f"Downside breakout pattern circumstances have been met")

    def check_trade(self, tick_type: str):
        if not self.ongoing_position:
            signal_result = self._check_signal()
            if signal_result in [PositionSide.LONG, PositionSide.SHORT]:
                self.open_position_with_market_order(signal_result)


