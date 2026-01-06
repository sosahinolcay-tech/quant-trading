import sys
from pathlib import Path
# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.param_sweep import sweep_and_save
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker
from qt.analytics.reports import summary_report


def main():
    # Run a simple parameter sweep with limited combinations for demo
    from itertools import product
    param_combos = list(product([0.5, 1.0], [0.0, 0.1]))
    sweep_and_save("simple", param_combos=param_combos, out_csv="notebooks/sweep_results.csv")
    print("Wrote notebooks/sweep_results.csv")
    # configure small execution fee and slippage for demo
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    mm = SimpleMarketMaker(symbol='X', base_spread=1.0)  # Use 'X' to match demo data
    eng.register_strategy(mm)
    eng.run_demo()
    # get equity curve from account
    eq = eng.account.get_equity_curve()
    if not eq:
        # fallback to initial cash if nothing recorded
        eq = [eng.account.cash, eng.account.cash]
    summary = summary_report(eq, out_csv_path='notebooks/summary_metrics.csv')
    print("Wrote notebooks/summary_metrics.csv ->", summary)


if __name__ == '__main__':
    main()
