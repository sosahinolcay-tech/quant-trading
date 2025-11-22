import sys
from pathlib import Path

# ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import AvellanedaMarketMaker
from qt.analytics.reports import summary_report


def main():
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    mm = AvellanedaMarketMaker(symbol='X', size=1.0, base_spread=0.02, risk_aversion=0.05, max_inventory=50)
    eng.register_strategy(mm)
    print('Running demo simulation (this may take a few seconds)...')
    eng.run_demo()

    # try to get equity curve; fallback to last price series
    try:
        eq = eng.account.get_equity_curve()
    except Exception:
        eq = []

    if not eq:
        # build a simple equity proxy from last_price history
        last = eng.order_book.last_price or 100.0
        eq = [last * 0.99, last]

    summary = summary_report(eq, out_csv_path='notebooks/summary_metrics_demo.csv')
    print('Demo summary:', summary)
    print('Trade count:', len(eng.trade_log))
    print('Turnover:', eng.turnover)


if __name__ == '__main__':
    main()
