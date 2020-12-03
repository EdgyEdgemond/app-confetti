from decimal import Decimal
from enum import IntEnum


class OrderType(IntEnum):
    BUY = 0
    SELL = 1
    BALANCE = 6


asset_pip = {
    "JPY": Decimal("0.01"),
    "XAU": Decimal("0.1"),
}
