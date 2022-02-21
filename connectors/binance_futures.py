import logging
import requests
import hmac
import hashlib
from urllib.parse import urlencode
import websocket
import time
import threading
import json
import typing

from strategies import Strategy, TechnicalStrategy, BreakoutStrategy
from connectors.binance_enums import *

from models import *

logger = logging.getLogger()


class BinanceFuturesClient:
    def __init__(self, public_api_key: str, secret_api_key: str, testnet: bool):
        self.public_api_key = public_api_key
        self.secret_api_key = secret_api_key
        if testnet:
            self.base_url = 'https://testnet.binancefuture.com'
            self.ws_base_url = 'wss://stream.binancefuture.com/ws'
        else:
            self.base_url = 'https://fapi.binance.com'
            self.ws_base_url = 'wss://fstream.binance.com/ws'

        self.contracts = self.get_contracts()
        self.balances = self.get_balances_info()
        self.prices = dict()
        self.strategies: typing.Dict[int: typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()
        self.logs_to_display = list()
        self._ws = None
        self._ws_stream_id = 1
        self._thread = threading.Thread(target=self.start_ws_connection)
        self._thread.start()
        logger.info('BinanceFuturesClient instance successfully constructed')

    def add_log(self, msg: str):
        self.logs_to_display.append({'log': msg, 'displayed': False})

    # TODO... need to improve it by making it more resilient to any potential issues.
    def _make_http_request(self, method: str, api_end_point: str, params=None, headers=None):
        logger.info('make_http_request method called')
        try:
            response = requests.request(method, self.base_url + api_end_point, params=params, headers=headers)
        except Exception as e:
            logger.error("Connection error occurred while making %s request to endpoint %s: %s", method, api_end_point, e)
            return None

        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError

    def generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self.secret_api_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    # returns typing.Dict[str, Contract]
    # str ---> like BTCUSDT. its the symbol in the contract object
    # Contract model ---> Contract object
    def get_contracts(self) -> typing.Dict[str, Contract]:
        logger.info('get_contracts method called')
        logger.info('getting the contracts')
        exchange_info = self._make_http_request('GET', '/fapi/v1/exchangeInfo')
        contracts = dict()
        if exchange_info is not None:
            symbols_list = exchange_info['symbols']
            for symbol in symbols_list:
                contracts[symbol['symbol']] = Contract(symbol)
            return contracts

    def get_bid_ask_price(self, contract: Contract) -> typing.Dict[str, float]:
        logger.info('get_bid_ask_price method called')
        params = dict()
        params['symbol'] = contract.symbol
        symbol_order_book_ticker = self._make_http_request('GET', '/fapi/v1/ticker/bookTicker', params)
        if symbol_order_book_ticker is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {
                    'ask': float(symbol_order_book_ticker['askPrice']),
                    'bid': float(symbol_order_book_ticker['bidPrice'])
                }
            else:
                self.prices[contract.symbol]['ask'] = float(symbol_order_book_ticker['askPrice'])
                self.prices[contract.symbol]['bid'] = float(symbol_order_book_ticker['bidPrice'])
            return self.prices[contract.symbol]

    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        logger.info('get_historical_candles method called')
        params = dict()
        params['symbol'] = contract.symbol
        params['interval'] = interval
        params['limit'] = 1000
        candlestick_raw_data = self._make_http_request('GET', '/fapi/v1/klines', params)
        if candlestick_raw_data is not None:
            return [Candle(
                raw_data={
                    'open_time': c[0],
                    'open': float(c[1]),
                    'high': float(c[2]),
                    'low': float(c[3]),
                    'close': float(c[4]),
                    'volume': float(c[5]),
                    'close_time': c[6],
                    'quote_asset_volume': float(c[7]),
                    'number_of_trades': float(c[8]),
                    'taker_buy_base_asset_volume': float(c[9]),
                    'taker_buy_quote_asset_volume': float(c[10]),
                    'ignore': float(c[11])
                }
            ) for c in candlestick_raw_data]

    # get balances from the current account information.
    def get_balances_info(self) -> typing.Dict[str, Asset]:
        logger.info('get_balances_info method called')
        params = dict()
        headers = dict()
        headers['X-MBX-APIKEY'] = self.public_api_key
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self.generate_signature(params)
        balances = dict()
        account_info = self._make_http_request('GET', '/fapi/v2/account', params=params, headers=headers)
        if account_info is not None:
            for raw_data in account_info['assets']:
                asset = Asset(raw_data)
                balances[asset.asset_name] = asset
        return balances

    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatusResponse:
        logger.info('get_order_status method called')
        params = dict()
        headers = dict()
        headers['X-MBX-APIKEY'] = self.public_api_key
        params['timestamp'] = int(time.time() * 1000)
        params['symbol'] = contract.symbol
        params['orderId'] = order_id
        params['signature'] = self.generate_signature(params)
        order_status = self._make_http_request('GET', '/fapi/v1/order', params=params, headers=headers)
        if order_status is not None:
            return OrderStatusResponse(order_status)

    def place_order(self, contract: Contract, side: OrderSide, quantity: float, order_type: OrderType, price=None,
                    time_in_force: typing.Union[TimeInForce, None] = None) -> OrderStatusResponse:
        logger.info(f'{self.place_order.__name__} method called')

        params = dict()
        headers = dict()
        headers['X-MBX-APIKEY'] = self.public_api_key
        params['timestamp'] = int(time.time() * 1000)
        params['symbol'] = contract.symbol
        params['side'] = side.name
        params['quantity'] = round(round(quantity / contract.lot_size) * contract.lot_size, 8)
        params['type'] = order_type.name

        if price is not None:
            params['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)

        if time_in_force is not None:
            params['timeInForce'] = time_in_force.name

        params['signature'] = self.generate_signature(params)

        place_order_status = self._make_http_request('POST', '/fapi/v1/order', params=params, headers=headers)

        if place_order_status is not None:
            return OrderStatusResponse(place_order_status)

    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatusResponse:
        logger.info('cancel_order method called')
        params = dict()
        headers = dict()
        headers['X-MBX-APIKEY'] = self.public_api_key
        params['timestamp'] = int(time.time() * 1000)
        params['orderId'] = order_id
        params['symbol'] = contract.symbol
        params['signature'] = self.generate_signature(params)
        cancel_order_response = self._make_http_request('DELETE', '/fapi/v1/order', params=params, headers=headers)
        if cancel_order_response is not None:
            return OrderStatusResponse(cancel_order_response)

    def start_ws_connection(self):
        websocket.enableTrace(False)
        self._ws = websocket.WebSocketApp(self.ws_base_url,
                                          on_open=self.on_open,
                                          on_message=self.on_message,
                                          on_error=self.on_error,
                                          on_close=self.on_close)
        while True:
            try:
                self._ws.run_forever()
            except Exception as e:
                logger.error('error in run_forever() method: %s', e)
                time.sleep(2)

    def on_message(self, ws, message: str):
        data = json.loads(message)
        # e refers to event type
        if 'e' in data:
            if data['e'] == 'bookTicker':
                symbol = data['s']
                if symbol not in self.prices:
                    self.prices[symbol] = {
                        'ask': float(data['a']),
                        'bid': float(data['b'])
                    }
                else:
                    self.prices[symbol]['ask'] = float(data['a'])
                    self.prices[symbol]['bid'] = float(data['b'])
            elif data['e'] == 'aggTrade':
                symbol = data['s']
                for key, strategy in self.strategies.items():
                    if strategy.contract.symbol == symbol:
                        result = strategy.parse_trades_to_update_current_candle(float(data['p']), float(data['q']), data['T'])
                        strategy.check_trade(result)
            else:
                return

    def on_error(self, ws, error):
        logger.error(error)

    def on_close(self, ws, close_status_code, close_msg):
        logger.info("### closed ###")

    def on_open(self, ws):
        logger.info("Binance connection opened")
        contracts_list = list(self.contracts.values())
        self.subscribe_to_stream('!bookTicker')

    def subscribe_to_stream(self, stream: str):
        logger.info("Subscribing to a stream %s", stream)
        payload = dict()
        payload['method'] = "SUBSCRIBE"
        payload['params'] = []
        payload['params'].append(stream)
        payload['id'] = self._ws_stream_id
        try:
            self._ws.send(json.dumps(payload))
        except Exception as e:
            logger.error("WebSocket connection error occurred while subscribing to stream %s", stream, e)
        self._ws_stream_id = self._ws_stream_id + 1

    def get_trade_size(self, contract: Contract, price: float, balance_percentage: float):
        balances = self.get_balances_info()
        if balances is not None:
            if 'USDT' in balances:
                usdt_wallet_balance = balances['USDT'].wallet_balance
            else:
                return None
        else:
            return None

        trade_size = (usdt_wallet_balance * balance_percentage / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)

        logger.info(f"Binance Futures current USDT balance: {usdt_wallet_balance} USDT, trade size of "
                    f"{contract.symbol}, price: {price} and balance percentage: {balance_percentage} "
                    f"is {trade_size}")

        return trade_size












