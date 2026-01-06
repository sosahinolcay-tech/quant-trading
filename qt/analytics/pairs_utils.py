import numpy as np
from statsmodels.tsa.stattools import adfuller


def fit_ols(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    A = np.vstack([x, np.ones(len(x))]).T
    beta, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(beta), float(intercept)


def is_cointegrated(x, y, alpha=0.05):
    # Augmented Dickey-Fuller on spread
    beta, intercept = fit_ols(x, y)
    spread = y - (beta * x + intercept)
    res = adfuller(spread)
    pvalue = float(res[1])
    return pvalue < alpha, pvalue
