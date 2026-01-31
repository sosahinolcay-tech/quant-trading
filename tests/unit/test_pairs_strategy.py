from qt.strategies.pairs import PairsStrategy
from qt.engine.event import MarketEvent


class MockEngine:
    def __init__(self):
        self.last_prices = {}
        self.order_books = {}

    def register_strategy(self, strat):
        pass


def test_pairs_strategy_init():
    eng = MockEngine()
    pairs = PairsStrategy("X", "Y")
    pairs.on_init(eng)
    assert pairs.symbol_x == "X"
    assert pairs.symbol_y == "Y"
    assert pairs.position == 0
    assert pairs.inventory_x == 0.0
    assert pairs.inventory_y == 0.0


def test_pairs_no_action_without_prices():
    eng = MockEngine()
    pairs = PairsStrategy("X", "Y")
    pairs.on_init(eng)
    orders = pairs.on_market_event(MarketEvent(0.0, "TRADE", "X", 100.0, 1.0, None))
    assert orders == []


def test_pairs_enters_position():
    eng = MockEngine()
    pairs = PairsStrategy("X", "Y", window=5, entry_z=1.0, exit_z=0.5)
    pairs.on_init(eng)
    # Simulate prices: X constant, Y increasing to create spread widening
    prices = [(100.0, 150.0), (100.0, 152.0), (100.0, 154.0), (100.0, 156.0), (100.0, 158.0), (100.0, 160.0)]
    for i, (px, py) in enumerate(prices):
        eng.last_prices["X"] = px
        eng.last_prices["Y"] = py
        orders = pairs.on_market_event(MarketEvent(float(i), "TRADE", "X", px, 1.0, None))
        if i < 4:
            assert orders == []  # not enough data
        elif i == 4:
            # Should enter short spread
            assert len(orders) == 2
            assert orders[0].symbol == "X"
            assert orders[0].side == "BUY"
            assert orders[1].symbol == "Y"
            assert orders[1].side == "SELL"
            assert pairs.position == -1


def test_pairs_exits_position():
    eng = MockEngine()
    pairs = PairsStrategy("X", "Y", window=5, entry_z=1.0, exit_z=0.5)
    pairs.on_init(eng)
    # Enter position first
    prices_enter = [(100.0, 150.0), (100.0, 152.0), (100.0, 154.0), (100.0, 156.0), (100.0, 158.0), (100.0, 160.0)]
    for i, (px, py) in enumerate(prices_enter):
        eng.last_prices["X"] = px
        eng.last_prices["Y"] = py
        orders = pairs.on_market_event(MarketEvent(float(i), "TRADE", "X", px, 1.0, None))
    assert pairs.position == -1
    # Now prices revert
    prices_exit = [(100.0, 155.0), (100.0, 152.0), (100.0, 150.0)]
    for i, (px, py) in enumerate(prices_exit, start=6):
        eng.last_prices["X"] = px
        eng.last_prices["Y"] = py
        orders = pairs.on_market_event(MarketEvent(float(i), "TRADE", "X", px, 1.0, None))
        if abs(pairs._compute_spread_z()) > 0.5:
            assert orders == []
        else:
            # Should exit
            assert len(orders) == 2
            assert orders[0].symbol == "X"
            assert orders[0].side == "SELL"
            assert orders[1].symbol == "Y"
            assert orders[1].side == "BUY"
            assert pairs.position == 0
            break


def test_pairs_inventory_update():
    eng = MockEngine()
    pairs = PairsStrategy("X", "Y")
    pairs.on_init(eng)
    # Simulate fill
    from qt.engine.event import FillEvent

    fill_buy_x = FillEvent("test", 0.0, "X", "BUY", 100.0, 10.0)
    fill_sell_y = FillEvent("test", 0.0, "Y", "SELL", 150.0, 15.0)
    pairs.on_order_filled(fill_buy_x)
    pairs.on_order_filled(fill_sell_y)
    assert pairs.inventory_x == 10.0
    assert pairs.inventory_y == -15.0
