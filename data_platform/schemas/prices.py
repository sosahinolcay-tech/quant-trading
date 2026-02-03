from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import BaseRecord


@dataclass(frozen=True)
class PriceBar(BaseRecord):
    price_open: float = 0.0
    price_high: float = 0.0
    price_low: float = 0.0
    price_close: float = 0.0
    volume: float = 0.0
    adjusted_close: Optional[float] = None
    split: Optional[float] = None
    dividend: Optional[float] = None


@dataclass(frozen=True)
class PriceQuery:
    symbol: str
    start: str
    end: str
    interval: str
    source: Optional[str] = None
