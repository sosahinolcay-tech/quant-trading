from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from data_platform.providers import AlphaVantageProvider, ProviderAdapter, YahooProvider
from data_platform.schemas import FundamentalsRecord, PriceBar, ProviderStatus
from data_platform.storage import save_price_bars, upsert_provider_status


def get_provider(name: str) -> ProviderAdapter:
    if name == "alpha_vantage":
        return AlphaVantageProvider()
    return YahooProvider()


def fetch_prices_and_store(
    provider_name: str,
    symbol: str,
    start: str,
    end: str,
    interval: str,
    storage_root: str,
    metadata_db: str,
) -> Tuple[List[PriceBar], ProviderStatus]:
    provider = get_provider(provider_name)
    start_ts = datetime.utcnow()
    bars, _raw = provider.fetch_prices(symbol, start, end, interval)
    latency = (datetime.utcnow() - start_ts).total_seconds() * 1000.0
    status = provider.fetch_status()
    status = ProviderStatus(
        name=status.name,
        status="ok" if bars else "empty",
        last_success=datetime.utcnow().isoformat() if bars else None,
        last_error=None if bars else "No data returned",
        last_latency_ms=latency,
        supported_domains=status.supported_domains,
        rate_limit=status.rate_limit,
    )
    upsert_provider_status(metadata_db, status)
    if bars:
        save_price_bars(bars, storage_root)
    return bars, status


def fetch_fundamentals(
    provider_name: str,
    symbol: str,
    period: str,
    metadata_db: str,
) -> Tuple[List[FundamentalsRecord], ProviderStatus]:
    provider = get_provider(provider_name)
    start_ts = datetime.utcnow()
    records = provider.fetch_fundamentals(symbol, period)
    latency = (datetime.utcnow() - start_ts).total_seconds() * 1000.0
    status = provider.fetch_status()
    status = ProviderStatus(
        name=status.name,
        status="ok" if records else "empty",
        last_success=datetime.utcnow().isoformat() if records else None,
        last_error=None if records else "No data returned",
        last_latency_ms=latency,
        supported_domains=status.supported_domains,
        rate_limit=status.rate_limit,
    )
    upsert_provider_status(metadata_db, status)
    return records, status
