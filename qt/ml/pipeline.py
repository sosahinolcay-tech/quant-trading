"""Simple ML pipeline: feature builder + model wrapper.

This is intentionally lightweight: a rolling feature builder that computes
returns and simple moving averages, and a model wrapper that uses
scikit-learn when available (via import) or a numpy linear-regression
fallback for predict/fit.
"""

from typing import Iterable, Tuple, Optional
import numpy as np

try:
    from sklearn.base import BaseEstimator
    from sklearn.linear_model import Ridge
    SKLEARN_AVAILABLE = True
except Exception:
    BaseEstimator = object
    Ridge = None
    SKLEARN_AVAILABLE = False


class FeatureBuilder:
    """Build windowed features from price series.

    Methods
    - rolling_returns: percentage returns over window
    - moving_average: simple moving average over window
    - build: combine features into X matrix and y target (next-step return)
    """

    def __init__(self, window: int = 10):
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window

    def rolling_returns(self, prices: Iterable[float]) -> np.ndarray:
        p = np.asarray(prices, dtype=float)
        if p.size < self.window + 1:
            return np.empty((0, self.window))
        rets = p[1:] / p[:-1] - 1.0
        X = np.lib.stride_tricks.sliding_window_view(rets, self.window)
        return X

    def moving_average(self, prices: Iterable[float]) -> np.ndarray:
        p = np.asarray(prices, dtype=float)
        if p.size < self.window:
            return np.empty((0,))
        c = np.convolve(p, np.ones(self.window)/self.window, mode="valid")
        return c

    def build(self, prices: Iterable[float]) -> Tuple[np.ndarray, np.ndarray]:
        p = np.asarray(prices, dtype=float)
        if p.size < self.window + 1:
            return np.empty((0, self.window+1)), np.empty((0,))

        rets = p[1:] / p[:-1] - 1.0
        # X1_full: rolling returns windows (length = len(rets)-window+1)
        X1_full = np.lib.stride_tricks.sliding_window_view(rets, self.window)
        # trim last row so that we can have a next-step return target
        if X1_full.shape[0] < 1:
            return np.empty((0, self.window+1)), np.empty((0,))
        X1 = X1_full[:-1]

        # align moving average: pick moving averages shifted by one to align
        ma_all = self.moving_average(p)
        # take slice starting at index 1 to align with X1 rows
        ma_slice = ma_all[1:1 + X1.shape[0]]
        if ma_slice.shape[0] < X1.shape[0]:
            # fallback: pad with last value
            pad_len = X1.shape[0] - ma_slice.shape[0]
            if ma_slice.size > 0:
                ma_slice = np.concatenate([ma_slice, np.repeat(ma_slice[-1], pad_len)])
            else:
                ma_slice = np.zeros((X1.shape[0],))

        X = np.hstack([X1, ma_slice.reshape(-1, 1)])
        # target: next-step return aligned with X1
        y = rets[self.window:self.window + X1.shape[0]]
        return X, y


class SimpleModelWrapper:
    """Wrapper that provides fit/predict around sklearn Ridge or numpy fallback.

    fit(X, y) stores model, predict(X) returns predictions.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.model: Optional[BaseEstimator] = None
        self.coef_: Optional[np.ndarray] = None
        if SKLEARN_AVAILABLE and Ridge is not None:
            self.model = Ridge(alpha=self.alpha)

    def fit(self, X: np.ndarray, y: np.ndarray):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        if X.size == 0:
            self.coef_ = np.zeros((X.shape[1],)) if X.ndim == 2 else np.array([])
            return self
        if self.model is not None:
            self.model.fit(X, y)
            try:
                self.coef_ = np.asarray(self.model.coef_)
            except Exception:
                self.coef_ = None
        else:
            # closed-form ridge regression
            n_features = X.shape[1]
            I = np.eye(n_features)
            A = X.T @ X + self.alpha * I
            b = X.T @ y
            self.coef_ = np.linalg.solve(A, b)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=float)
        if X.size == 0:
            return np.empty((0,))
        if self.model is not None:
            return self.model.predict(X)
        if self.coef_ is None:
            raise RuntimeError("Model is not fitted")
        return X @ self.coef_
