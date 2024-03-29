from utilities import *
from connectors.binance_enums import *
from enums import *


# it is referred to it in the udemy class as Balance
class Asset:
    def __init__(self, raw_data):
        self.asset_name = raw_data['asset']  # asset name like "USDT"
        self.wallet_balance = float(raw_data["walletBalance"])  # wallet balance
        self.margin_balance = float(raw_data["marginBalance"])  # margin balance
        self.initial_margin = float(raw_data["initialMargin"])  # total initial margin required with current mark price
        self.unrealized_pnl = float(raw_data["unrealizedProfit"])  # unrealized profit
        self.maintenance_margin = float(raw_data["maintMargin"])  # maintenance margin required


class Candle:
    def __init__(self, raw_data: dict):
        self.open_time = raw_data['open_time']  # Open time, its referred to as timestamp of the candle
        self.open = raw_data['open']  # Open
        self.high = raw_data['high']  # High
        self.low = raw_data['low']  # Low
        self.close = raw_data['close']  # Close
        self.volume = raw_data['volume']  # Volume
        self.close_time = raw_data['close_time']  # Close time
        self.quote_asset_volume = check_if_key_exists_in_dict('quote_asset_volume', raw_data)  # Quote asset volume
        self.number_of_trades = check_if_key_exists_in_dict('number_of_trades', raw_data)  # Number of trades
        self.taker_buy_base_asset_volume = check_if_key_exists_in_dict('taker_buy_base_asset_volume', raw_data)  # Taker buy base asset volume
        self.taker_buy_quote_asset_volume = check_if_key_exists_in_dict('taker_buy_quote_asset_volume', raw_data)  # Taker buy quote asset volume
        self.ignore = check_if_key_exists_in_dict('ignore', raw_data) # Ignore


class Contract:
    def __init__(self, raw_data, exchange: Exchanges):
        self.symbol = raw_data["symbol"]
        self.pair = raw_data['pair']
        self.base_asset = raw_data['baseAsset']
        self.quote_asset = raw_data['quoteAsset']
        self.price_decimals = raw_data["pricePrecision"]  # please do not use it as tickSize
        self.quantity_decimals = raw_data["quantityPrecision"]  # please do not use it as stepSize
        self.tick_size = 1 / pow(10, raw_data['pricePrecision'])
        self.lot_size = 1 / pow(10, raw_data['quantityPrecision'])
        self.exchange: Exchanges = exchange


class OrderStatusResponse:
    def __init__(self, raw_data):
        self.avg_price = float(raw_data["avgPrice"])
        self.status: OrderStatus = OrderStatus[raw_data['status']]
        self.order_id = raw_data['orderId']


class Trade:
    def __init__(self, time: int, contract: Contract, strategy: str, side: OrderSide, entry_price: float,
                 status: TradeStatus, pnl: float, quantity, entry_id):
        self.time: int = time
        self.contract: Contract = contract
        self.strategy: str = strategy
        self.side: OrderSide = side
        self.entry_price: float = entry_price
        self.status: TradeStatus = status
        self.pnl: float = pnl
        self.quantity = quantity
        self.entry_id = entry_id
