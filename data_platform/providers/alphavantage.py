from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

import pandas as pd
import requests

from data_platform.schemas import FundamentalsRecord, PriceBar, ProviderStatus
from .base import ProviderAdapter


class AlphaVantageProvider(ProviderAdapter):
    name = "alpha_vantage"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def _key(self) -> str:
        key = self.api_key or ""
        if not key:
            import os

            key = os.getenv("ALPHAVANTAGE_API_KEY", "")
        if not key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY is required")
        return key

    def fetch_prices(
        self, symbol: str, start: str, end: str, interval: str
    ) -> Tuple[List[PriceBar], Optional[pd.DataFrame]]:
        key = self._key()
        if interval.endswith("m"):
            function = "TIME_SERIES_INTRADAY"
            av_interval = interval
        else:
            function = "TIME_SERIES_DAILY_ADJUSTED"
            av_interval = None

        params = {
            "function": function,
            "symbol": symbol,
            "apikey": key,
            "outputsize": "compact",
        }
        if av_interval:
            params["interval"] = av_interval

        resp = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        time_key = None
        for k in data.keys():
            if "Time Series" in k:
                time_key = k
                break
        if not time_key:
            return [], None

        series = data.get(time_key, {})
        rows = []
        for ts, vals in series.items():
            rows.append(
                {
                    "timestamp": pd.to_datetime(ts, errors="coerce"),
                    "open": float(vals.get("1. open", 0.0)),
                    "high": float(vals.get("2. high", 0.0)),
                    "low": float(vals.get("3. low", 0.0)),
                    "close": float(vals.get("4. close", 0.0)),
                    "volume": float(vals.get("6. volume", vals.get("5. volume", 0.0))),
                }
            )
        df = pd.DataFrame(rows).dropna(subset=["timestamp"])
        if df.empty:
            return [], None

        df["timestamp"] = df["timestamp"].astype("int64") // 10**9
        ingested_at = datetime.utcnow()
        bars: List[PriceBar] = []
        for row in df.itertuples():
            bars.append(
                PriceBar(
                    symbol=symbol,
                    timestamp=float(row.timestamp),
                    source=self.name,
                    timezone="UTC",
                    ingested_at=ingested_at,
                    price_open=float(row.open),
                    price_high=float(row.high),
                    price_low=float(row.low),
                    price_close=float(row.close),
                    volume=float(row.volume),
                )
            )
        return bars, df

    def fetch_fundamentals(self, symbol: str, period: str) -> List[FundamentalsRecord]:
        key = self._key()
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": key,
        }
        resp = requests.get("https://www.alphavantage.co/query", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data or "Symbol" not in data:
            return []

        ingested_at = datetime.utcnow()
        record = FundamentalsRecord(
            symbol=symbol,
            timestamp=ingested_at.timestamp(),
            source=self.name,
            timezone="UTC",
            currency=data.get("Currency"),
            ingested_at=ingested_at,
            fiscal_period=period,
            revenue=_to_float(data.get("RevenueTTM")),
            ebitda=_to_float(data.get("EBITDA")),
            net_income=_to_float(data.get("NetIncomeTTM")),
            eps=_to_float(data.get("EPS")),
            assets=_to_float(data.get("TotalAssets")),
            liabilities=_to_float(data.get("TotalLiabilities")),
            equity=_to_float(data.get("ShareholderEquity")),
        )
        return [record]

    def fetch_status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            status="ok",
            supported_domains=["prices", "fundamentals"],
            rate_limit="5 requests/min free tier",
        )


def _to_float(val):
    try:
        return float(val)
    except Exception:
        return None
