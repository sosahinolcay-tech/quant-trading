import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
from tools.param_sweep import sweep_and_save
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import AvellanedaMarketMaker
from qt.analytics.reports import full_report
from qt.analytics.reporting import generate_run_report
from qt.utils.run_artifacts import save_run_artifacts


def main():
    # Run a simple parameter sweep with limited combinations for demo
    from itertools import product

    param_combos = list(product([0.5, 1.0], [0.0, 0.1]))
    sweep_and_save("simple", param_combos=param_combos, out_csv="notebooks/sweep_results.csv")
    print("Wrote notebooks/sweep_results.csv")
    # configure small execution fee and slippage for demo
    eng = SimulationEngine(
        execution_fee=float(os.getenv("EXEC_FEE", "0.0005")),
        slippage_coeff=float(os.getenv("EXEC_SLIPPAGE", "0.0001")),
        half_spread_bps=float(os.getenv("EXEC_HALF_SPREAD_BPS", "2")),
        impact_coeff=float(os.getenv("EXEC_IMPACT", "0.0001")),
    )
    symbol = os.getenv("MM_SYMBOL", "AAPL")
    risk_aversion = float(os.getenv("MM_RISK_AVERSION", "0.1"))
    max_inventory = float(os.getenv("MM_MAX_INVENTORY", "100"))
    mm = AvellanedaMarketMaker(
        symbol=symbol,
        risk_aversion=risk_aversion,
        max_inventory=max_inventory,
        base_spread=0.01,
    )
    eng.register_strategy(mm)
    data_source = os.getenv("DATA_SOURCE", "yahoo")
    start_date = os.getenv("START_DATE", "2024-01-01")
    end_date = os.getenv("END_DATE", "2024-06-01")
    interval = os.getenv("INTERVAL", "1m")
    if interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = "5d"
    eng.run_demo(data_source=data_source, start_date=start_date, end_date=end_date, interval=interval)
    # get equity curve from account
    eq_hist = eng.account.equity_history
    if not eq_hist:
        # fallback to initial cash if nothing recorded
        eq_hist = [(0.0, eng.account.cash), (1.0, eng.account.cash)]
    summary = full_report(
        eq_hist,
        trade_log=eng.trade_log,
        exposure_history=eng.account.exposure_history,
        out_csv_path="notebooks/summary_metrics_demo.csv",
    )
    generate_run_report("market_maker_run", summary, eq_hist, eng.trade_log)
    save_run_artifacts(
        "market_maker_run",
        {
            "symbol": symbol,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "execution_fee": eng.account.fee,
        },
        summary,
        eq_hist,
        eng.trade_log,
    )
    print("Wrote notebooks/summary_metrics_demo.csv ->", summary)

    if eq_hist:
        import csv

        with open("notebooks/equity_demo.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "equity"])
            for ts, val in eq_hist:
                writer.writerow([ts, val])
        print("Equity curve saved to notebooks/equity_demo.csv")


if __name__ == "__main__":
    main()
