from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd

from data_platform.schemas import FundamentalsRecord, PriceBar, ProviderStatus
from .base import ProviderAdapter


class YahooProvider(ProviderAdapter):
    name = "yahoo"

    def fetch_prices(
        self, symbol: str, start: str, end: str, interval: str
    ) -> Tuple[List[PriceBar], Optional[pd.DataFrame]]:
        try:
            import yfinance as yf
        except Exception as exc:
            raise RuntimeError("yfinance is required for YahooProvider") from exc

        df = yf.download(
            symbol,
            start=start,
            end=end,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        if df is None or df.empty:
            return [], None

        df = df.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        ts_col = None
        for candidate in ("Datetime", "Date", "index"):
            if candidate in df.columns:
                ts_col = candidate
                break
        if not ts_col:
            raise RuntimeError("Yahoo data missing date column")
        df["timestamp"] = pd.to_datetime(df[ts_col], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["timestamp"] = df["timestamp"].astype("int64") // 10**9

        bars: List[PriceBar] = []
        ingested_at = datetime.utcnow()
        for row in df.itertuples():
            bars.append(
                PriceBar(
                    symbol=symbol,
                    timestamp=float(row.timestamp),
                    source=self.name,
                    timezone="UTC",
                    currency=None,
                    ingested_at=ingested_at,
                    price_open=float(getattr(row, "Open", 0.0) or 0.0),
                    price_high=float(getattr(row, "High", 0.0) or 0.0),
                    price_low=float(getattr(row, "Low", 0.0) or 0.0),
                    price_close=float(getattr(row, "Close", 0.0) or 0.0),
                    volume=float(getattr(row, "Volume", 0.0) or 0.0),
                    adjusted_close=float(getattr(row, "Adj_Close", getattr(row, "Adj Close", None)) or 0.0),
                    dividend=float(getattr(row, "Dividends", 0.0) or 0.0),
                    split=float(getattr(row, "Stock_Splits", getattr(row, "Stock Splits", None)) or 0.0),
                )
            )
        return bars, df

    def fetch_fundamentals(self, symbol: str, period: str) -> List[FundamentalsRecord]:
        try:
            import yfinance as yf
        except Exception as exc:
            raise RuntimeError("yfinance is required for YahooProvider") from exc

        ticker = yf.Ticker(symbol)
        info = ticker.get_info() if hasattr(ticker, "get_info") else ticker.info
        if not info:
            return []

        ingested_at = datetime.utcnow()
        record = FundamentalsRecord(
            symbol=symbol,
            timestamp=ingested_at.timestamp(),
            source=self.name,
            timezone="UTC",
            currency=info.get("currency"),
            ingested_at=ingested_at,
            fiscal_period=period,
            revenue=info.get("totalRevenue"),
            ebitda=info.get("ebitda"),
            net_income=info.get("netIncomeToCommon"),
            eps=info.get("trailingEps"),
            assets=info.get("totalAssets"),
            liabilities=info.get("totalLiab"),
            equity=info.get("totalStockholderEquity"),
        )
        return [record]

    def fetch_status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            status="ok",
            supported_domains=["prices", "fundamentals"],
        )
