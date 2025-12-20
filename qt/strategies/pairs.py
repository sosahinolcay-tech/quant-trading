from .base import StrategyBase
from ..analytics.statistics import adf_test
from ..engine.event import OrderEvent
import numpy as np
from typing import Deque
import collections


class PairsStrategy(StrategyBase):
    """Cointegration-based pairs trading strategy with rolling OLS hedge ratio."""

    def __init__(self, symbol_x: str, symbol_y: str, window: int = 100, entry_z: float = 2.0, exit_z: float = 0.5, quantity: float = 100.0):
        super().__init__(symbol_x)
        self.symbol_x = symbol_x
        self.symbol_y = symbol_y
        self.window = window
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.quantity = quantity
        self.prices_x: Deque[float] = collections.deque(maxlen=window)
        self.prices_y: Deque[float] = collections.deque(maxlen=window)
        self.beta = 0.0
        self.intercept = 0.0
        self.position = 0  # -1 short spread, 0 flat, +1 long spread
        self.inventory_x = 0.0
        self.inventory_y = 0.0
        self._order_seq = 0

    def _next_order_id(self):
        self._order_seq += 1
        return f"pairs-{self._order_seq}"

    def on_init(self, engine):
        super().on_init(engine)

    def _fit_ols(self):
        x = np.array([float(v) for v in self.prices_x], dtype=float)
        y = np.array([float(v) for v in self.prices_y], dtype=float)
        if len(x) < 2:
            return
        A = np.vstack([x, np.ones(len(x))]).T
        beta, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        self.beta = float(beta)
        self.intercept = float(intercept)

    def _compute_spread_z(self):
        if len(self.prices_x) < 2:
            return 0.0
        x = np.array([float(v) for v in self.prices_x], dtype=float)
        y = np.array([float(v) for v in self.prices_y], dtype=float)
        spread = y - (self.beta * x + self.intercept)
        mean = spread.mean()
        std = spread.std(ddof=1) if len(spread) > 1 else 1.0
        z = (spread[-1] - mean) / (std + 1e-9)
        return float(z)

    def on_market_event(self, event):
        # Use engine's last_prices per symbol
        px = self.engine.last_prices.get(self.symbol_x, None)
        py = self.engine.last_prices.get(self.symbol_y, None)
        # only append if values are present
        if px is not None and py is not None:
            try:
                self.prices_x.append(float(px))
                self.prices_y.append(float(py))
            except Exception:
                return []
        if len(self.prices_x) >= self.window and len(self.prices_y) >= self.window:
            self._fit_ols()
            z = self._compute_spread_z()
            orders = []
            t = event.timestamp
            qty_x = self.quantity
            qty_y = max(1, round(self.beta * qty_x))
            if self.position == 0 and z > self.entry_z:
                # short spread: short y, long x
                self.position = -1
                orders = [
                    OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_x, side="BUY", price=px, quantity=qty_x, order_type="MARKET"),
                    OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_y, side="SELL", price=py, quantity=qty_y, order_type="MARKET"),
                ]
            elif self.position == 0 and z < -self.entry_z:
                # long spread: long y, short x
                self.position = 1
                orders = [
                    OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_x, side="SELL", price=px, quantity=qty_x, order_type="MARKET"),
                    OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_y, side="BUY", price=py, quantity=qty_y, order_type="MARKET"),
                ]
            elif self.position != 0 and abs(z) < self.exit_z:
                # close position
                if self.position == -1:
                    # was short spread, now buy y, sell x
                    orders = [
                        OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_x, side="SELL", price=px, quantity=abs(self.inventory_x), order_type="MARKET"),
                        OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_y, side="BUY", price=py, quantity=abs(self.inventory_y), order_type="MARKET"),
                    ]
                elif self.position == 1:
                    # was long spread, now sell y, buy x
                    orders = [
                        OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_x, side="BUY", price=px, quantity=abs(self.inventory_x), order_type="MARKET"),
                        OrderEvent(order_id=self._next_order_id(), timestamp=t, symbol=self.symbol_y, side="SELL", price=py, quantity=abs(self.inventory_y), order_type="MARKET"),
                    ]
                self.position = 0
            return orders
        return []

    def on_order_filled(self, fill):
        if fill.symbol == self.symbol_x:
            if fill.side == "BUY":
                self.inventory_x += fill.quantity
            else:
                self.inventory_x -= fill.quantity
        elif fill.symbol == self.symbol_y:
            if fill.side == "BUY":
                self.inventory_y += fill.quantity
            else:
                self.inventory_y -= fill.quantity

