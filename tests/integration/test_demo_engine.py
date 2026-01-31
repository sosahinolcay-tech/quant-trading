from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker


def test_demo_runs():
    eng = SimulationEngine()
    strat = SimpleMarketMaker(symbol="X", size=1.0, base_spread=1.0)
    eng.register_strategy(strat)
    eng.run_demo()
    # if no exceptions and engine has order books, assume success
    assert len(eng.order_books) > 0
