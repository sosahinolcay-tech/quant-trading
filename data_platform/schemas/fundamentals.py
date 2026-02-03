from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .base import BaseRecord


@dataclass(frozen=True)
class FundamentalsRecord(BaseRecord):
    fiscal_period: Optional[str] = None
    fiscal_date: Optional[str] = None
    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    equity: Optional[float] = None


@dataclass(frozen=True)
class FundamentalsQuery:
    symbol: str
    period: str
    source: Optional[str] = None
