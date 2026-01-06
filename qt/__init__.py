"""Quant Trading Framework

A comprehensive event-driven quantitative trading simulator with market making
and pairs trading strategies.
"""

__version__ = "0.1.0"

from . import analytics
from . import engine
from . import risk
from . import strategies
from . import utils

__all__ = ["analytics", "engine", "risk", "strategies", "utils"]
