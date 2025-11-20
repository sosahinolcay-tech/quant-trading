
from ..engine.event import OrderEvent
from .base import StrategyBase
import collections
import math


class SimpleMarketMaker(StrategyBase):
    """Market maker with volatility-based spread and inventory penalty.

    This is a light approximation of Avellaneda-Stoikov ideas for demo purposes.
    """

    def __init__(self, symbol: str, size: float = 1.0, base_spread: float = 1.0, inventory_coeff: float = 0.1, vol_window: int = 10):
        super().__init__(symbol)
        self.size = size
        self.base_spread = base_spread
        self.inventory_coeff = inventory_coeff
        self.vol_window = vol_window
        self._order_seq = 0
        self.prices = collections.deque(maxlen=vol_window)
        self.inventory = 0.0

    def _next_order_id(self):
        self._order_seq += 1
        return f"mm-{self._order_seq}"

    def _estimate_vol(self):
        if len(self.prices) < 2:
            return 0.0
        rets = [ (self.prices[i+1] / self.prices[i] - 1.0) for i in range(len(self.prices)-1) ]
        # use simple std dev of returns annualized assuming 252 trading days
        vol = (sum((r - (sum(rets)/len(rets)))**2 for r in rets) / (len(rets)-1))**0.5 if len(rets)>1 else 0.0
        return vol * math.sqrt(252)

    def on_market_event(self, event):
        # update price history for vol estimate
        if event.price and event.price > 0:
            self.prices.append(event.price)

        mid = self.engine.order_book.mid_price()
        if mid == 0:
            return []

        vol = self._estimate_vol()
        # dynamic spread: base + k*vol
        k = 1.0
        spread = self.base_spread + k * vol

        # inventory penalty shifts quotes to reduce inventory
        penalty = self.inventory_coeff * self.inventory
        bid = mid - spread/2.0 - penalty
        ask = mid + spread/2.0 - penalty
        t = event.timestamp
        orders = [
            OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol, side="BUY", price=bid, quantity=self.size, order_type="LIMIT"),
            OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol, side="SELL", price=ask, quantity=self.size, order_type="LIMIT"),
        ]
        return orders

    def on_order_filled(self, fill):
        # simple inventory update: buy increases inventory, sell decreases
        if fill.side == "BUY":
            self.inventory += fill.quantity
        else:
            self.inventory -= fill.quantity

