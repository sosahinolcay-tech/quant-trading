import numpy as np


def size_by_volatility(target_vol, price_series, min_size=0.1, max_size=10.0):
    """Scale position size to target a volatility level."""
    prices = np.asarray(price_series, dtype=float)
    if prices.size < 3:
        return 1.0
    rets = prices[1:] / np.maximum(prices[:-1], 1e-12) - 1.0
    vol = np.std(rets, ddof=1)
    if vol <= 1e-12:
        return 1.0
    size = target_vol / vol
    return float(np.clip(size, min_size, max_size))
