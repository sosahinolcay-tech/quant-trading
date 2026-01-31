import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
from qt.engine.engine import SimulationEngine
from qt.strategies.pairs import PairsStrategy
from qt.analytics.reports import full_report
from qt.analytics.reporting import generate_run_report
from qt.utils.run_artifacts import save_run_artifacts


def main():
    eng = SimulationEngine(
        execution_fee=float(os.getenv("EXEC_FEE", "0.0005")),
        slippage_coeff=float(os.getenv("EXEC_SLIPPAGE", "0.0001")),
        half_spread_bps=float(os.getenv("EXEC_HALF_SPREAD_BPS", "2")),
        impact_coeff=float(os.getenv("EXEC_IMPACT", "0.0001")),
    )
    symbol_x = os.getenv("PAIRS_SYMBOL_X", "MSFT")
    symbol_y = os.getenv("PAIRS_SYMBOL_Y", "AAPL")
    window = int(os.getenv("PAIRS_WINDOW", "30"))
    entry_z = float(os.getenv("PAIRS_ENTRY_Z", "1.0"))
    exit_z = float(os.getenv("PAIRS_EXIT_Z", "0.2"))
    quantity = float(os.getenv("PAIRS_QUANTITY", "10.0"))
    pairs = PairsStrategy(
        symbol_x=symbol_x,
        symbol_y=symbol_y,
        window=window,
        entry_z=entry_z,
        exit_z=exit_z,
        quantity=quantity,
        min_vol=float(os.getenv("PAIRS_MIN_VOL", "0.0003")),
        trend_window=int(os.getenv("PAIRS_TREND_WINDOW", "30")),
        max_trend_slope=float(os.getenv("PAIRS_MAX_TREND", "0.002")),
    )
    eng.register_strategy(pairs)
    print("Running pairs demo simulation (this may take a few seconds)...")
    data_source = os.getenv("DATA_SOURCE", "yahoo")
    start_date = os.getenv("START_DATE", "2024-01-01")
    end_date = os.getenv("END_DATE", "2024-06-01")
    interval = os.getenv("INTERVAL", "1m")
    if interval in {"1m", "2m", "5m"} and not os.getenv("YAHOO_RANGE"):
        os.environ["YAHOO_RANGE"] = "5d"
    eng.run_demo(data_source=data_source, start_date=start_date, end_date=end_date, interval=interval)

    # try to get equity curve; fallback to last price series
    try:
        eq = eng.account.equity_history  # list of (timestamp, equity)
    except Exception:
        eq = []

    if not eq:
        eq = [(0.0, 100000.0), (1.0, 100000.0)]  # flat if no trades

    summary = full_report(
        eq,
        trade_log=eng.trade_log,
        exposure_history=eng.account.exposure_history,
        out_csv_path="notebooks/summary_metrics_pairs_demo.csv",
    )
    generate_run_report("pairs_run", summary, eq, eng.trade_log)
    save_run_artifacts(
        "pairs_run",
        {
            "symbol_x": symbol_x,
            "symbol_y": symbol_y,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "execution_fee": eng.account.fee,
        },
        summary,
        eq,
        eng.trade_log,
    )
    print("Pairs demo summary:", summary)
    print("Trade count:", len(eng.trade_log))
    print("Turnover:", eng.turnover)

    # Save equity curve for plotting
    if eq:
        import csv

        with open("notebooks/equity_pairs_demo.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "equity"])
            for ts, val in eq:
                writer.writerow([ts, val])
        print("Equity curve saved to notebooks/equity_pairs_demo.csv")


if __name__ == "__main__":
    main()
