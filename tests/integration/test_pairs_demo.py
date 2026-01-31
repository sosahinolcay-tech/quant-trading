from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker
from qt.strategies.pairs import PairsStrategy


def test_pairs_demo_runs():
    eng = SimulationEngine()
    mm = SimpleMarketMaker(symbol="X", base_spread=0.5, inventory_coeff=0.1)
    ps = PairsStrategy("X", "Y", window=20)
    eng.register_strategy(mm)
    eng.register_strategy(ps)
    eng.run_demo()
    assert "X" in eng.last_prices and "Y" in eng.last_prices
