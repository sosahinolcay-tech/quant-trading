from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class MarketEvent:
    timestamp: float
    type: Literal["TRADE", "QUOTE", "SNAPSHOT"]
    symbol: str
    price: float
    size: float
    side: Optional[Literal["BUY", "SELL"]]


@dataclass
class OrderEvent:
    order_id: str
    timestamp: float
    symbol: str
    side: Literal["BUY", "SELL"]
    price: float
    quantity: float
    order_type: Literal["LIMIT", "MARKET"]


@dataclass
class FillEvent:
    order_id: str
    timestamp: float
    symbol: Optional[str]
    side: Literal["BUY", "SELL"]
    price: float
    quantity: float
    fee: float = 0.0
