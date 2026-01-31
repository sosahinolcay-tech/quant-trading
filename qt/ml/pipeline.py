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
    """Build windowed features from price series."""

    def __init__(
        self,
        window: int = 10,
        ma_window: int = 20,
        vol_window: int = 20,
        rsi_window: int = 14,
        boll_window: int = 20,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        momentum_window: int = 10,
    ):
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window
        self.ma_window = ma_window
        self.vol_window = vol_window
        self.rsi_window = rsi_window
        self.boll_window = boll_window
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.momentum_window = momentum_window

    @staticmethod
    def _ema(series: np.ndarray, span: int) -> np.ndarray:
        alpha = 2.0 / (span + 1.0)
        out = np.zeros_like(series)
        out[0] = series[0]
        for i in range(1, len(series)):
            out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
        return out

    def build(self, prices: Iterable[float]) -> Tuple[np.ndarray, np.ndarray]:
        p = np.asarray(prices, dtype=float)
        if p.size < max(self.window + 2, self.macd_slow + 2, self.boll_window + 2):
            return np.empty((0, 0)), np.empty((0,))

        rets = p[1:] / p[:-1] - 1.0
        n = len(rets)
        min_lookback = max(
            self.window,
            self.ma_window,
            self.vol_window,
            self.rsi_window,
            self.boll_window,
            self.macd_slow,
            self.momentum_window,
        )

        ema_fast = self._ema(p, self.macd_fast)
        ema_slow = self._ema(p, self.macd_slow)
        macd = ema_fast - ema_slow
        macd_signal = self._ema(macd, self.macd_signal)

        X_rows = []
        y_vals = []
        for i in range(min_lookback - 1, n - 2):
            end_idx = i + 1  # aligns with price index
            ret_window = rets[end_idx - self.window:end_idx]
            if ret_window.shape[0] != self.window:
                continue

            ma_slice = p[end_idx + 1 - self.ma_window:end_idx + 1]
            vol_slice = rets[end_idx + 1 - self.vol_window:end_idx + 1]
            boll_slice = p[end_idx + 1 - self.boll_window:end_idx + 1]

            ma = ma_slice.mean()
            vol = np.std(vol_slice, ddof=1)
            momentum = p[end_idx] / p[end_idx - self.momentum_window] - 1.0

            gains = np.clip(rets[end_idx + 1 - self.rsi_window:end_idx + 1], 0, None)
            losses = -np.clip(rets[end_idx + 1 - self.rsi_window:end_idx + 1], None, 0)
            avg_gain = gains.mean()
            avg_loss = losses.mean()
            rs = avg_gain / max(avg_loss, 1e-12)
            rsi = 100.0 - 100.0 / (1.0 + rs)

            boll_mean = boll_slice.mean()
            boll_std = np.std(boll_slice, ddof=1)
            boll_z = (p[end_idx] - boll_mean) / max(boll_std, 1e-12)

            feature_row = np.hstack(
                [
                    ret_window,
                    np.array(
                        [
                            ma,
                            vol,
                            momentum,
                            rsi,
                            macd[end_idx],
                            macd_signal[end_idx],
                            boll_z,
                        ],
                        dtype=float,
                    ),
                ]
            )
            X_rows.append(feature_row)
            y_vals.append(rets[end_idx + 1])

        X = np.asarray(X_rows, dtype=float)
        y = np.asarray(y_vals, dtype=float)
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
