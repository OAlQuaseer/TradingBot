from enum import Enum


class Exchanges(Enum):
    BINANCE = 'Binance'
    BITMEX = 'Bitmex'


class TradeStatus(Enum):
    OPEN = 1
    CLOSED = 2
