import numpy as np

from qt.analytics.metrics import compute_cagr, compute_calmar, compute_drawdown_duration, compute_return_stats


def test_return_stats_and_cagr():
    eq = [100.0, 105.0, 110.0, 120.0]
    stats = compute_return_stats(np.array([0.05, 0.0476, 0.0909]))
    assert "mean" in stats and "std" in stats
    cagr = compute_cagr(eq, annualization=3.0)
    assert isinstance(cagr, float)


def test_drawdown_duration():
    eq = [100.0, 110.0, 90.0, 95.0, 120.0]
    duration = compute_drawdown_duration(eq)
    assert duration["max_duration"] >= 1


def test_calmar_ratio():
    eq = [100.0, 110.0, 90.0, 95.0, 120.0]
    calmar = compute_calmar(eq, annualization=4.0)
    assert isinstance(calmar, float)
