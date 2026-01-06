"""Lightweight ML utilities for Week 4.

This module provides a small feature builder and a model wrapper that
uses scikit-learn when available and falls back to a simple numpy
least-squares predictor otherwise so tests and examples work without
installing heavy ML dependencies.
"""

from .pipeline import FeatureBuilder, SimpleModelWrapper

__all__ = ["FeatureBuilder", "SimpleModelWrapper"]
