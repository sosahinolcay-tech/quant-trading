from typing import List, Tuple


class OrderBook:
    """Minimal top-of-book order book for demo/testing."""

    def __init__(self):
        # simple representation: best bid, best ask as tuples (price, size)
        self.best_bid = (0.0, 0.0)
        self.best_ask = (0.0, 0.0)
        self.last_price = 0.0

    def update_from_snapshot(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        if bids:
            self.best_bid = bids[0]
        if asks:
            self.best_ask = asks[0]

    def apply_trade(self, price: float, size: float):
        self.last_price = price

    def mid_price(self) -> float:
        b, a = self.best_bid[0], self.best_ask[0]
        if b <= 0 or a <= 0:
            return self.last_price
        return (b + a) / 2.0

    # minimal API for adding a limit order (not full matching engine)
    def add_limit_order(self, side: str, price: float, qty: float):
        # return a fake order id
        return f"ord-{int(price*100)}-{int(qty)}"

    def process_trade(self, price: float, size: float):
        # for testing return a fill summary
        return [{"price": price, "quantity": size}]
