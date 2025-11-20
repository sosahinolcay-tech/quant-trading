from abc import ABC, abstractmethod


class StrategyBase(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.engine = None

    def on_init(self, engine):
        self.engine = engine

    @abstractmethod
    def on_market_event(self, event):
        """Process MarketEvent and optionally return list of OrderEvent to place."""
        return []

    def on_order_filled(self, fill):
        return None
