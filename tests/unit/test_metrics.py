import numpy as np
from qt.analytics.metrics import compute_returns, compute_sharpe, compute_drawdown, rolling_sharpe


def test_compute_returns_and_sharpe():
    eq = [100.0, 101.0, 100.5, 102.0]
    rets = compute_returns(eq)
    assert len(rets) == 3
    # simple sanity: last return
    assert abs(rets[-1] - (102.0 / 100.5 - 1.0)) < 1e-9
    sr = compute_sharpe(rets, annualization=252.0)
    assert isinstance(sr, float)


def test_drawdown_and_rolling():
    eq = [100.0, 110.0, 90.0, 95.0, 120.0]
    dd = compute_drawdown(eq)
    assert "max_drawdown" in dd
    rolls = rolling_sharpe(eq, window=2)
    # rolling_sharpe returns an array aligned to equity length
    assert isinstance(rolls, (list, np.ndarray))
