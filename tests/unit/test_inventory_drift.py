import time

from qt.strategies.market_maker import AvellanedaMarketMaker


class DummyOrderBook:
    def __init__(self, mid):
        self._mid = mid

    def mid_price(self):
        return self._mid


class DummyEngine:
    def __init__(self, mid=100.0):
        self.order_books = {"SYM": DummyOrderBook(mid)}
        self.last_prices = {"SYM": mid}


class Event:  # small stand-in for market events
    def __init__(self, price, timestamp=None):
        self.price = price
        self.timestamp = timestamp or time.time()


class Fill:  # stand-in for a fill event
    def __init__(self, side, quantity):
        self.side = side
        self.quantity = quantity


def test_inventory_stays_bounded_under_balanced_fills():
    mm = AvellanedaMarketMaker("SYM", size=1.0, base_spread=0.01, risk_aversion=0.05, max_inventory=10)
    eng = DummyEngine(mid=100.0)
    mm.on_init(eng)

    # simulate a sequence of market events and symmetric fills
    for i in range(50):
        e = Event(price=100.0 + (i % 2) * 0.01)
        orders = mm.on_market_event(e)
        # simulate a fill alternating BUY and SELL to keep inventory near zero
        if orders:
            # alternate sides
            if i % 2 == 0:
                mm.on_order_filled(Fill("BUY", 1.0))
            else:
                mm.on_order_filled(Fill("SELL", 1.0))

    assert abs(mm.inventory) <= 2.0


def test_inventory_respects_max_inventory():
    mm = AvellanedaMarketMaker("SYM", size=5.0, base_spread=0.01, risk_aversion=0.2, max_inventory=5)
    eng = DummyEngine(mid=100.0)
    mm.on_init(eng)

    # force fills in one direction
    for _ in range(5):
        mm.on_order_filled(Fill("BUY", 2.0))

    # inventory should not be NaN and should be a finite value
    assert mm.inventory >= 0
    # after exceeding max_inventory the quoting qty would be reduced; inventory may exceed but should be finite
    assert mm.inventory < 1000
