from __future__ import annotations

import os
import pandas as pd

from qt.engine.engine import SimulationEngine
from qt.engine.event import MarketEvent
from qt.strategies.pairs import PairsStrategy
from qt.analytics.metrics import compute_returns, compute_sharpe
from qt.data import get_prices_with_quality


def walk_forward_intraday(
    symbol_x: str,
    symbol_y: str,
    interval: str = "1m",
    range_str: str = "5d",
    n_windows: int = 5,
    window_size: int = 60,
    test_size: int = 30,
):
    os.environ.setdefault("YAHOO_RANGE", range_str)
    df_x, _ = get_prices_with_quality("yahoo", symbol_x, "2024-01-01", "2024-06-01", interval=interval)
    df_y, _ = get_prices_with_quality("yahoo", symbol_y, "2024-01-01", "2024-06-01", interval=interval)
    if df_x is None or df_y is None:
        return []

    df = pd.merge(df_x[["timestamp", "price"]], df_y[["timestamp", "price"]], on="timestamp", suffixes=("_x", "_y"))
    prices_x = df["price_x"].values
    prices_y = df["price_y"].values
    n_total = len(df)
    if n_total < (window_size + test_size) * n_windows:
        return []

    results = []
    for w in range(n_windows):
        start = w * (window_size + test_size)
        test_slice = slice(start + window_size, start + window_size + test_size)

        eng = SimulationEngine(
            execution_fee=float(os.getenv("EXEC_FEE", "0.0005")),
            slippage_coeff=float(os.getenv("EXEC_SLIPPAGE", "0.0001")),
            half_spread_bps=float(os.getenv("EXEC_HALF_SPREAD_BPS", "2")),
            impact_coeff=float(os.getenv("EXEC_IMPACT", "0.0001")),
        )
        ps = PairsStrategy(symbol_x, symbol_y, window=window_size, entry_z=1.0, exit_z=0.2, quantity=10.0)
        eng.register_strategy(ps)

        for i in range(test_slice.start, test_slice.stop):
            evx = MarketEvent(timestamp=float(i), type="TRADE", symbol=symbol_x, price=float(prices_x[i]), size=1.0, side=None)
            evy = MarketEvent(timestamp=float(i), type="TRADE", symbol=symbol_y, price=float(prices_y[i]), size=1.0, side=None)
            eng._process_market_event(evx)
            eng._process_market_event(evy)

        equity_curve = eng.account.get_equity_curve()
        if equity_curve and len(equity_curve) > 1:
            rets = compute_returns(equity_curve)
            sharpe = compute_sharpe(rets)
            final_eq = equity_curve[-1]
        else:
            sharpe = 0.0
            final_eq = 100000.0

        window_result = {
            "window": w + 1,
            "sharpe": sharpe,
            "final_equity": final_eq,
            "trades": len(eng.trade_log),
            "turnover": eng.turnover,
        }
        results.append(window_result)
    return results
