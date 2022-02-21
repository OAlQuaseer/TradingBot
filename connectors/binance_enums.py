from enum import Enum


class OrderSide(Enum):
    BUY = 1
    SELL = 2


class PositionSide(Enum):
    BOTH = 1
    LONG = 2
    SHORT = 3


class OrderStatus(Enum):
    NEW = 1
    PARTIALLY_FILLED = 2
    FILLED = 3
    CANCELED = 4
    REJECTED = 5
    EXPIRED = 6


class OrderType(Enum):
    LIMIT = 1
    MARKET = 2
    STOP = 3
    STOP_MARKET = 4
    TAKE_PROFIT = 5
    TAKE_PROFIT_MARKET = 6
    TRAILING_STOP_MARKET = 7


class TimeInForce(Enum):
    GTC = 1  # Good Till Cancel
    IOC = 2  # Immediate or Cancel
    FOK = 3  # Fill or Kill
    GTX = 4  # Good Till Crossing(Post Only)

