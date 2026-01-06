from abc import ABC, abstractmethod
from typing import List, Any, Optional
from ..engine.event import MarketEvent, FillEvent


class StrategyBase(ABC):
    """Base class for trading strategies.
    
    All trading strategies should inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(self, symbol: str):
        """Initialize strategy with a symbol.
        
        Args:
            symbol: Trading symbol this strategy operates on
        """
        self.symbol = symbol
        self.engine: Optional[Any] = None

    def on_init(self, engine: Any) -> None:
        """Called when strategy is registered with the engine.
        
        Args:
            engine: SimulationEngine instance
        """
        self.engine = engine

    @abstractmethod
    def on_market_event(self, event: MarketEvent) -> List[Any]:
        """Process MarketEvent and optionally return list of OrderEvent to place.
        
        Args:
            event: MarketEvent to process
        
        Returns:
            List of OrderEvent objects to place (empty list if none)
        """
        return []

    def on_order_filled(self, fill: FillEvent) -> None:
        """Called when an order placed by this strategy is filled.
        
        Args:
            fill: FillEvent containing fill details
        
        Default implementation does nothing. Override in subclasses
        to track positions, update state, etc.
        """
        return None
