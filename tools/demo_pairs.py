import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qt.engine.engine import SimulationEngine
from qt.strategies.pairs import PairsStrategy
from qt.analytics.reports import full_report


def main():
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    pairs = PairsStrategy(symbol_x='X', symbol_y='Y', window=50, entry_z=1.5, exit_z=0.5, quantity=10.0)
    eng.register_strategy(pairs)
    print('Running pairs demo simulation (this may take a few seconds)...')
    eng.run_demo()

    # try to get equity curve; fallback to last price series
    try:
        eq = eng.account.get_equity_curve()
    except Exception:
        eq = []

    if not eq:
        # build a simple equity proxy from last_price history
        last_x = eng.last_prices.get('X', 100.0)
        last_y = eng.last_prices.get('Y', 150.0)
        eq = [(0.0, 100000.0), (1.0, 100000.0)]  # flat if no trades

    summary = full_report(eq, trade_log=eng.trade_log, out_csv_path='notebooks/summary_metrics_pairs_demo.csv')
    print('Pairs demo summary:', summary)
    print('Trade count:', len(eng.trade_log))
    print('Turnover:', eng.turnover)


if __name__ == '__main__':
    main()