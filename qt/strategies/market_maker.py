"""Market-making strategies.

This module provides a lightweight Avellaneda-like market maker suitable for
backtesting. It keeps the external `SimpleMarketMaker` behavior but adds a
more configurable `AvellanedaMarketMaker` with EWMA volatility, reservation
price shift for inventory control, adaptive quoting frequency, and safety
limits.
"""

from ..engine.event import OrderEvent
from .base import StrategyBase
import collections
import math
import time
from typing import Optional, Deque, Any

# Constants
TRADING_DAYS_PER_YEAR = 252
MIN_TICK_SIZE = 1e-8


class SimpleMarketMaker(StrategyBase):
    """Legacy simple market maker kept for compatibility.

    Behavior preserved from the earlier implementation: volatility-based
    spread with a linear inventory penalty shifting quotes.
    """

    def __init__(
        self, symbol: str, size: float = 1.0, base_spread: float = 1.0, inventory_coeff: float = 0.1, vol_window: int = 10
    ):
        super().__init__(symbol)
        self.size = size
        self.base_spread = base_spread
        self.inventory_coeff = inventory_coeff
        self.vol_window = vol_window
        self._order_seq = 0
        self.prices: Deque[float] = collections.deque(maxlen=vol_window)
        self.inventory = 0.0

    def _next_order_id(self):
        self._order_seq += 1
        return f"mm-{self._order_seq}"

    def _estimate_vol(self):
        if len(self.prices) < 2:
            return 0.0
        rets = [(self.prices[i + 1] / self.prices[i] - 1.0) for i in range(len(self.prices) - 1)]
        vol = (sum((r - (sum(rets) / len(rets))) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5 if len(rets) > 1 else 0.0
        return vol * math.sqrt(TRADING_DAYS_PER_YEAR)

    def on_market_event(self, event):
        # update price history for vol estimate
        if getattr(event, "price", None) and event.price > 0:
            self.prices.append(event.price)

        mid = self.engine.order_books.get(
            self.symbol, type("Dummy", (), {"mid_price": lambda _: self.engine.last_prices.get(self.symbol, 100.0)})()
        ).mid_price()
        if not mid:
            return []

        vol = self._estimate_vol()
        k = 1.0
        spread = max(self.base_spread + k * vol, 1e-6)

        penalty = self.inventory_coeff * self.inventory
        bid = mid - spread / 2.0 - penalty
        ask = mid + spread / 2.0 - penalty
        t = getattr(event, "timestamp", time.time())
        orders = [
            OrderEvent(
                order_id=self._next_order_id(),
                timestamp=t,
                symbol=self.symbol,
                side="BUY",
                price=bid,
                quantity=self.size,
                order_type="LIMIT",
            ),
            OrderEvent(
                order_id=self._next_order_id(),
                timestamp=t,
                symbol=self.symbol,
                side="SELL",
                price=ask,
                quantity=self.size,
                order_type="LIMIT",
            ),
        ]
        return orders

    def on_order_filled(self, fill):
        if fill.side == "BUY":
            self.inventory += fill.quantity
        else:
            self.inventory -= fill.quantity


class AvellanedaMarketMaker(SimpleMarketMaker):
    """A compact Avellaneda-like market maker.

    This implementation approximates the reservation price / optimal spread
    ideas from Avellaneda & Stoikov. It is intentionally lightweight and
    parameterized to be easy to tune in parameter sweeps.

    Key parameters
    - risk_aversion: higher -> wider spreads and stronger inventory control
    - max_inventory: safety limit where quoting reduces or stops
    - ewma_alpha: for EWMA volatility estimator
    - min_quote_interval: minimum seconds between quote updates (adaptive)
    """

    def __init__(
        self,
        symbol: str,
        size: float = 1.0,
        base_spread: float = 0.01,
        risk_aversion: float = 0.1,
        max_inventory: float = 100.0,
        vol_window: int = 50,
        ewma_alpha: float = 0.2,
        min_quote_interval: float = 0.1,
    ):
        super().__init__(symbol, size=size, base_spread=base_spread, inventory_coeff=risk_aversion, vol_window=vol_window)
        self.risk_aversion = risk_aversion
        self.max_inventory = max_inventory
        self.ewma_alpha = ewma_alpha
        self.ewma_vol = 0.0
        self._last_quote_time: Optional[float] = None
        self.min_quote_interval = min_quote_interval

    def _update_ewma_vol(self, price: float):
        # maintain EWMA of absolute log returns
        if len(self.prices) >= 1:
            last = self.prices[-1]
            if last > 0:
                lr = math.log(price / last)
                r = abs(lr)
                self.ewma_vol = (1 - self.ewma_alpha) * self.ewma_vol + self.ewma_alpha * r
        else:
            self.ewma_vol = 0.0

    def _adaptive_interval(self):
        # increase quoting interval when vol is high to avoid churn
        factor = 1.0 + (self.ewma_vol * 50.0)
        return self.min_quote_interval * factor

    def _reservation_price_and_spread(self, mid: float):
        # reservation price (r) shifted against inventory to encourage mean reversion
        inventory = self.inventory
        sigma = max(self.ewma_vol, 1e-9)
        # simple reservation price shift: proportional to inventory and risk_aversion
        r = mid - inventory * self.risk_aversion * sigma
        # optimal spread approx: base + gamma * sigma
        optimal_spread = max(self.base_spread + self.risk_aversion * sigma, 1e-6)
        return r, optimal_spread

    def on_market_event(self, event):
        price = getattr(event, "price", None)
        if price and price > 0:
            self.prices.append(price)
            self._update_ewma_vol(price)

        mid = self.engine.order_books.get(
            self.symbol, type("Dummy", (), {"mid_price": lambda _: self.engine.last_prices.get(self.symbol, 100.0)})()
        ).mid_price()
        if not mid:
            return []

        now = getattr(event, "timestamp", time.time())
        if self._last_quote_time is None:
            self._last_quote_time = now - 9999.0

        interval = self._adaptive_interval()
        if now - self._last_quote_time < interval:
            # throttle quoting to avoid excessive churn
            return []

        self._last_quote_time = now

        r, spread = self._reservation_price_and_spread(mid)

        # shift quotes so that inventory is reduced: bid < r < ask
        half = spread / 2.0
        bid = r - half
        ask = r + half

        # safety clipping: avoid negative or crossed quotes
        min_tick = max(MIN_TICK_SIZE, mid * 1e-6)
        bid = max(bid, min_tick)
        ask = max(ask, bid + min_tick)

        # if inventory is extreme, reduce size or stop quoting
        qty = self.size
        if abs(self.inventory) >= self.max_inventory:
            qty = max(0.0, self.size * (1.0 - (abs(self.inventory) - self.max_inventory) / (self.max_inventory + 1e-9)))

        t = now
        orders = []
        if qty > 0:
            orders = [
                OrderEvent(
                    order_id=self._next_order_id(),
                    timestamp=t,
                    symbol=self.symbol,
                    side="BUY",
                    price=bid,
                    quantity=qty,
                    order_type="LIMIT",
                ),
                OrderEvent(
                    order_id=self._next_order_id(),
                    timestamp=t,
                    symbol=self.symbol,
                    side="SELL",
                    price=ask,
                    quantity=qty,
                    order_type="LIMIT",
                ),
            ]

        return orders

    def on_order_filled(self, fill):
        # update inventory same as base class but respect direction
        super().on_order_filled(fill)
