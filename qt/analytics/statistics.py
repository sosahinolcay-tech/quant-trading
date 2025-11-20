import numpy as np
from statsmodels.tsa.stattools import adfuller
from typing import Tuple


def adf_test(series):
    res = adfuller(series)
    return {"adf_stat": float(res[0]), "pvalue": float(res[1]), "usedlag": int(res[2])}


def bootstrap_sharpe_ci(returns, n_boot=1000, alpha=0.05) -> Tuple[float, float]:
    # simple bootstrap on returns to get CI for Sharpe
    returns = np.array(returns)
    if len(returns) == 0:
        return (0.0, 0.0)
    n = len(returns)
    shs = []
    for _ in range(n_boot):
        sample = np.random.choice(returns, size=n, replace=True)
        sr = np.mean(sample) / (np.std(sample, ddof=1) + 1e-9) * np.sqrt(252.0)
        shs.append(sr)
    lower = float(np.percentile(shs, 100 * alpha / 2))
    upper = float(np.percentile(shs, 100 * (1 - alpha / 2)))
    return lower, upper
