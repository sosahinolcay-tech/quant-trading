import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
from qt.engine.engine import SimulationEngine
from qt.strategies.pairs import PairsStrategy
from qt.analytics.reports import full_report


def main():
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    symbol_x = os.getenv("PAIRS_SYMBOL_X", "MSFT")
    symbol_y = os.getenv("PAIRS_SYMBOL_Y", "AAPL")
    window = int(os.getenv("PAIRS_WINDOW", "60"))
    entry_z = float(os.getenv("PAIRS_ENTRY_Z", "1.5"))
    exit_z = float(os.getenv("PAIRS_EXIT_Z", "0.5"))
    quantity = float(os.getenv("PAIRS_QUANTITY", "10.0"))
    pairs = PairsStrategy(
        symbol_x=symbol_x,
        symbol_y=symbol_y,
        window=window,
        entry_z=entry_z,
        exit_z=exit_z,
        quantity=quantity,
    )
    eng.register_strategy(pairs)
    print("Running pairs demo simulation (this may take a few seconds)...")
    data_source = os.getenv("DATA_SOURCE", "yahoo")
    start_date = os.getenv("START_DATE", "2022-01-01")
    end_date = os.getenv("END_DATE", "2024-01-01")
    interval = os.getenv("INTERVAL", "1d")
    eng.run_demo(data_source=data_source, start_date=start_date, end_date=end_date, interval=interval)

    # try to get equity curve; fallback to last price series
    try:
        eq = eng.account.equity_history  # list of (timestamp, equity)
    except Exception:
        eq = []

    if not eq:
        eq = [(0.0, 100000.0), (1.0, 100000.0)]  # flat if no trades

    summary = full_report(eq, trade_log=eng.trade_log, out_csv_path="notebooks/summary_metrics_pairs_demo.csv")
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
