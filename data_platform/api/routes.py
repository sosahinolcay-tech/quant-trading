from __future__ import annotations

from typing import List

import os
from io import StringIO
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from data_platform.api.service import fetch_fundamentals, fetch_prices_and_store
from data_platform.storage import list_provider_status

router = APIRouter()


class PricesRequest(BaseModel):
    symbol: str
    start: str
    end: str
    interval: str = "1d"
    source: str = "yahoo"
    limit: Optional[int] = None
    offset: Optional[int] = None


class FundamentalsRequest(BaseModel):
    symbol: str
    period: str = "annual"
    source: str = "yahoo"
    limit: Optional[int] = None
    offset: Optional[int] = None


def _check_api_key(api_key: Optional[str]) -> None:
    expected = os.getenv("PLATFORM_API_KEY")
    if not expected:
        return
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _paginate(items: List[dict], limit: Optional[int], offset: Optional[int]) -> List[dict]:
    start = max(offset or 0, 0)
    end = start + limit if limit else None
    return items[start:end]


def _as_csv(rows: List[dict]) -> PlainTextResponse:
    df = pd.DataFrame(rows)
    buf = StringIO()
    df.to_csv(buf, index=False)
    return PlainTextResponse(buf.getvalue(), media_type="text/csv")


@router.post("/data/prices", response_model=List[dict])
def prices(
    req: PricesRequest,
    response: Response,
    format: str = "json",
    x_api_key: Optional[str] = Header(default=None),
):
    _check_api_key(x_api_key)
    _set_rate_headers(response)
    bars, _status = fetch_prices_and_store(
        req.source,
        req.symbol,
        req.start,
        req.end,
        req.interval,
        storage_root="platform_data/prices",
        metadata_db="platform_data/metadata.sqlite",
    )
    rows = _paginate([b.to_dict() for b in bars], req.limit, req.offset)
    if format == "csv":
        return _as_csv(rows)
    return rows


@router.post("/data/fundamentals", response_model=List[dict])
def fundamentals(
    req: FundamentalsRequest,
    response: Response,
    format: str = "json",
    x_api_key: Optional[str] = Header(default=None),
):
    _check_api_key(x_api_key)
    _set_rate_headers(response)
    records, _status = fetch_fundamentals(
        req.source,
        req.symbol,
        req.period,
        metadata_db="platform_data/metadata.sqlite",
    )
    rows = _paginate([r.to_dict() for r in records], req.limit, req.offset)
    if format == "csv":
        return _as_csv(rows)
    return rows


@router.get("/providers/status", response_model=List[dict])
def providers_status(response: Response, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    _set_rate_headers(response)
    statuses = list_provider_status("platform_data/metadata.sqlite")
    return [s.__dict__ for s in statuses]


@router.get("/data/news", response_model=List[dict])
def news(response: Response, x_api_key: Optional[str] = Header(default=None)):
    _check_api_key(x_api_key)
    _set_rate_headers(response)
    return []


def _set_rate_headers(response: Response) -> None:
    limit = os.getenv("PLATFORM_RATE_LIMIT", "1000")
    response.headers["X-RateLimit-Limit"] = limit
    response.headers["X-RateLimit-Remaining"] = limit
