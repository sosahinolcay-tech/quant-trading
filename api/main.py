from __future__ import annotations

from typing import Optional, List, Dict, Any

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import AvellanedaMarketMaker
from qt.strategies.pairs import PairsStrategy
from qt.analytics.reports import full_report
from qt.data import get_prices_with_quality
from qt.analytics.walk_forward import walk_forward_intraday

app = FastAPI(title="Quant Trading API", version="0.1.0")


def _expected_freq_seconds(interval: str) -> Optional[int]:
    mapping = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800, "60m": 3600, "1h": 3600, "1d": 86400}
    return mapping.get(interval)


def _serialize_equity(eq_history) -> List[Dict[str, float]]:
    return [{"timestamp": float(ts), "equity": float(eq)} for ts, eq in eq_history]


def _serialize_trades(trade_log) -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": float(t.get("timestamp", 0.0)),
            "order_id": t.get("order_id"),
            "symbol": t.get("symbol"),
            "side": t.get("side"),
            "price": float(t.get("price", 0.0)),
            "quantity": float(t.get("quantity", 0.0)),
            "fee": float(t.get("fee", 0.0)),
        }
        for t in trade_log
    ]


class MarketMakerRequest(BaseModel):
    symbol: str = "AAPL"
    interval: str = "1m"
    start_date: str = "2024-01-01"
    end_date: str = "2024-06-01"
    size: float = 5.0
    base_spread: float = 0.02
    risk_aversion: float = 0.1
    max_inventory: float = 50.0
    data_source: str = "yahoo"
    execution_fee: float = 0.0005
    slippage_coeff: float = 0.0001
    half_spread_bps: float = 2.0
    impact_coeff: float = 0.0001


class PairsRequest(BaseModel):
    symbol_x: str = "MSFT"
    symbol_y: str = "AAPL"
    interval: str = "1m"
    start_date: str = "2024-01-01"
    end_date: str = "2024-06-01"
    window: int = 30
    entry_z: float = 1.0
    exit_z: float = 0.2
    quantity: float = 10.0
    min_vol: float = 0.0003
    trend_window: int = 30
    max_trend_slope: float = 0.002
    data_source: str = "yahoo"
    execution_fee: float = 0.0005
    slippage_coeff: float = 0.0001
    half_spread_bps: float = 2.0
    impact_coeff: float = 0.0001


class QualityRequest(BaseModel):
    symbol: str = "AAPL"
    interval: str = "1m"
    start_date: str = "2024-01-01"
    end_date: str = "2024-06-01"
    data_source: str = "yahoo"


class WalkForwardRequest(BaseModel):
    symbol_x: str = "MSFT"
    symbol_y: str = "AAPL"
    interval: str = "1m"
    range_str: str = "5d"
    n_windows: int = 5
    window_size: int = 60
    test_size: int = 30


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/data/quality")
def data_quality(req: QualityRequest) -> Dict[str, Any]:
    if req.interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = "5d"
    df, report = get_prices_with_quality(
        req.data_source,
        req.symbol,
        req.start_date,
        req.end_date,
        interval=req.interval,
        expected_freq_seconds=_expected_freq_seconds(req.interval),
    )
    if df is None:
        raise HTTPException(status_code=404, detail="No data returned from data source.")
    return {"symbol": req.symbol, "interval": req.interval, "report": report}


@app.post("/run/market-maker")
def run_market_maker(req: MarketMakerRequest) -> Dict[str, Any]:
    if req.interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = "5d"
    eng = SimulationEngine(
        execution_fee=req.execution_fee,
        slippage_coeff=req.slippage_coeff,
        half_spread_bps=req.half_spread_bps,
        impact_coeff=req.impact_coeff,
    )
    mm = AvellanedaMarketMaker(
        symbol=req.symbol,
        size=req.size,
        base_spread=req.base_spread,
        risk_aversion=req.risk_aversion,
        max_inventory=req.max_inventory,
    )
    eng.register_strategy(mm)
    eng.run_demo(data_source=req.data_source, start_date=req.start_date, end_date=req.end_date, interval=req.interval)
    eq_hist = eng.account.equity_history
    summary = full_report(eq_hist, trade_log=eng.trade_log, exposure_history=eng.account.exposure_history)
    return {"summary": summary, "equity": _serialize_equity(eq_hist), "trades": _serialize_trades(eng.trade_log)}


@app.post("/run/pairs")
def run_pairs(req: PairsRequest) -> Dict[str, Any]:
    if req.interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = "5d"
    eng = SimulationEngine(
        execution_fee=req.execution_fee,
        slippage_coeff=req.slippage_coeff,
        half_spread_bps=req.half_spread_bps,
        impact_coeff=req.impact_coeff,
    )
    ps = PairsStrategy(
        req.symbol_x,
        req.symbol_y,
        window=req.window,
        entry_z=req.entry_z,
        exit_z=req.exit_z,
        quantity=req.quantity,
        min_vol=req.min_vol,
        trend_window=req.trend_window,
        max_trend_slope=req.max_trend_slope,
    )
    eng.register_strategy(ps)
    eng.run_demo(data_source=req.data_source, start_date=req.start_date, end_date=req.end_date, interval=req.interval)
    eq_hist = eng.account.equity_history
    summary = full_report(eq_hist, trade_log=eng.trade_log, exposure_history=eng.account.exposure_history)
    return {"summary": summary, "equity": _serialize_equity(eq_hist), "trades": _serialize_trades(eng.trade_log)}


@app.post("/walk-forward")
def run_walk_forward(req: WalkForwardRequest) -> Dict[str, Any]:
    if req.interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = req.range_str
    results = walk_forward_intraday(
        symbol_x=req.symbol_x,
        symbol_y=req.symbol_y,
        interval=req.interval,
        range_str=req.range_str,
        n_windows=req.n_windows,
        window_size=req.window_size,
        test_size=req.test_size,
    )
    return {"results": results}
