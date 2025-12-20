"""Momentum strategy that can use a trained ML model for signals.

Implements a simple strategy that builds features from recent prices
and uses a provided model wrapper with `predict` to create a signal.
If no model is provided, it falls back to a pure momentum rule.
"""

from typing import Optional, List, Literal
from .base import StrategyBase
from ..engine.event import OrderEvent
from ..ml.pipeline import FeatureBuilder, SimpleModelWrapper
import time
import numpy as np


class MomentumModelStrategy(StrategyBase):
    def __init__(self, symbol: str, window: int = 10, size: float = 1.0, model: Optional[SimpleModelWrapper] = None):
        super().__init__(symbol)
        self.window = window
        self.size = size
        self.prices: List[float] = []
        self.model = model
        self.fb = FeatureBuilder(window=window)

    def on_init(self, engine):
        super().on_init(engine)

    def _signal_from_model(self) -> float:
        X, _ = self.fb.build(self.prices)
        if X.shape[0] == 0:
            return 0.0
        x_last = X[-1:].reshape(1, -1)
        if self.model is None:
            # fallback: sum of recent returns
            return float(np.sign(x_last[0, :self.window].sum()))
        pred = self.model.predict(x_last)
        return float(np.sign(pred[0]))

    def on_market_event(self, event) -> List[OrderEvent]:
        price = getattr(event, "price", None)
        if price is None or price <= 0:
            return []
        self.prices.append(price)
        # keep memory bounded
        if len(self.prices) > max(1000, self.window * 10):
            self.prices.pop(0)

        sig = self._signal_from_model()
        if sig == 0.0:
            return []

        side: Literal["BUY", "SELL"] = "BUY" if sig > 0 else "SELL"
        t = getattr(event, "timestamp", time.time())
        order = OrderEvent(order_id=f"mom-1", timestamp=t, symbol=self.symbol, side=side, price=price, quantity=self.size, order_type="MARKET")
        return [order]

    def on_order_filled(self, fill):
        return None
