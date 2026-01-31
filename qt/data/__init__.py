"""Data sources for market data with validation and caching."""

from __future__ import annotations

from typing import Optional
import os
import time
import pandas as pd
import numpy as np
from ..utils.logger import get_logger

from .cache import cache_key, read_cache, write_cache
from .prep import prepare_price_frame, data_quality_report
from .yahoo_api import fetch_yahoo_chart

logger = get_logger(__name__)


class DataSource:
    """Base class for data sources."""

    def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """Get historical price data for symbol."""
        raise NotImplementedError


class YahooFinanceDataSource(DataSource):
    """Yahoo Finance data source using yfinance with caching."""

    def __init__(self, use_cache: bool = True, min_rows: int = 10):
        self.use_cache = use_cache
        self.min_rows = min_rows

    def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        key = cache_key("yahoo", symbol, start_date, end_date, interval)
        if self.use_cache:
            cached = read_cache(key)
            if cached is not None and not cached.empty:
                prepared, issues = prepare_price_frame(cached, min_rows=self.min_rows)
                if not issues:
                    return prepared
        try:
            import yfinance as yf

            df = None
            for attempt in range(3):
                ticker = yf.Ticker(symbol)
                df = ticker.history(start=start_date, end=end_date, interval=interval)
                if df is not None and not df.empty:
                    break
                time.sleep(0.5 * (attempt + 1))

            if df is None or df.empty:
                for attempt in range(3):
                    df = yf.download(
                        symbol,
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        progress=False,
                        auto_adjust=True,
                        threads=False,
                    )
                    if df is not None and not df.empty:
                        break
                    time.sleep(0.5 * (attempt + 1))

            if df is None or df.empty:
                period = os.getenv("YAHOO_PERIOD", "2y")
                for attempt in range(3):
                    df = yf.download(
                        symbol,
                        period=period,
                        interval=interval,
                        progress=False,
                        auto_adjust=True,
                        threads=False,
                    )
                    if df is not None and not df.empty:
                        break
                    time.sleep(0.5 * (attempt + 1))

            if df is None or df.empty:
                range_str = os.getenv("YAHOO_RANGE", "2y")
                df = fetch_yahoo_chart(symbol, interval=interval, range_str=range_str)

            if df is None or df.empty:
                logger.warning(f"Yahoo Finance returned no data for {symbol}.")
                return None

            prepared, issues = prepare_price_frame(df, min_rows=self.min_rows)
            if issues:
                logger.warning(f"Yahoo Finance data issues for {symbol}: {issues}")
                return None
            if self.use_cache:
                write_cache(key, prepared)
            return prepared
        except Exception as exc:
            logger.warning(f"Yahoo Finance fetch failed for {symbol}: {exc}")
            return None


class SyntheticDataSource(DataSource):
    """Synthetic data generator with volatility clustering and jumps."""

    def __init__(self, min_rows: int = 10):
        self.min_rows = min_rows

    def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        np.random.seed(hash(symbol) % 2**32)  # Deterministic seed per symbol

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        days = (end - start).days
        if days <= 0:
            days = 252

        freq = "D" if interval in ("1d", "1D", "day") else "H"
        timestamps = pd.date_range(start=start, periods=days, freq=freq)
        prices = [100.0]

        vol = 0.015
        drift = 0.0002
        for _ in range(len(timestamps) - 1):
            vol = 0.8 * vol + 0.2 * abs(np.random.normal(0, 0.02))
            jump = np.random.normal(0, 0.05) if np.random.rand() < 0.02 else 0.0
            ret = drift + np.random.normal(0, vol) + jump
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 0.01))

        df = pd.DataFrame(
            {
                "timestamp": timestamps.astype(np.int64) // 10**9,
                "price": prices,
            }
        )
        prepared, _ = prepare_price_frame(df, min_rows=self.min_rows)
        return prepared


def get_data_source(source_type: str = "yahoo") -> DataSource:
    """Factory for data sources."""
    if source_type == "yahoo":
        return YahooFinanceDataSource()
    return SyntheticDataSource()


def get_prices_with_quality(
    source_type: str,
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "1d",
    expected_freq_seconds: Optional[int] = None,
) -> tuple[Optional[pd.DataFrame], dict]:
    ds = get_data_source(source_type)
    df = ds.get_prices(symbol, start_date, end_date, interval=interval)
    if df is None or df.empty:
        return None, {}
    report = data_quality_report(df, expected_freq_seconds=expected_freq_seconds)
    return df, report
