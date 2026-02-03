from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import pandas as pd

from data_platform.schemas import FundamentalsRecord, PriceBar, ProviderStatus


class ProviderAdapter(ABC):
    name: str

    @abstractmethod
    def fetch_prices(
        self, symbol: str, start: str, end: str, interval: str
    ) -> Tuple[List[PriceBar], Optional[pd.DataFrame]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_fundamentals(self, symbol: str, period: str) -> List[FundamentalsRecord]:
        raise NotImplementedError

    @abstractmethod
    def fetch_status(self) -> ProviderStatus:
        raise NotImplementedError
