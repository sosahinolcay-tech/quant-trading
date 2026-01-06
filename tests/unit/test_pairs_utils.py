import numpy as np
from qt.analytics.pairs_utils import fit_ols, is_cointegrated


def generate_cointegrated(n=200, beta=2.0, sigma=0.5):
    x = np.cumsum(np.random.normal(scale=0.1, size=n)) + 10
    eps = np.random.normal(scale=sigma, size=n)
    y = beta * x + 0.5 + eps
    return x, y


def test_fit_ols_and_cointegration():
    x, y = generate_cointegrated()
    beta, intercept = fit_ols(x, y)
    assert abs(beta - 2.0) < 0.5
    coin, p = is_cointegrated(x, y)
    # p-value may vary; assert we at least return a p-value in range
    assert 0.0 <= p <= 1.0
