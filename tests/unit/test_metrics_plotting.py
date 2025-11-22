import numpy as np
import pytest

from qt.analytics.metrics import rolling_sharpe, plot_equity_curve, plot_drawdown, plot_rolling_sharpe


def test_rolling_sharpe_padding():
    # create a simple equity curve
    eq = list(100 + np.cumsum(np.random.normal(scale=0.5, size=50)))
    series = rolling_sharpe(eq, window=10)
    # same length as equity
    assert len(series) == len(eq)
    # first element should be NaN (no returns yet)
    assert np.isnan(series[0])
    # before window completes there should be NaNs
    assert np.all(np.isnan(series[1:9]))


def test_plotting_helpers_smoke():
    eq = list(100 + np.cumsum(np.random.normal(scale=0.5, size=60)))
    try:
        ax = plot_equity_curve(eq)
        assert ax is not None
        ax2 = plot_drawdown(eq)
        assert ax2 is not None
        ax3 = plot_rolling_sharpe(eq, window=10)
        assert ax3 is not None
    except ImportError:
        pytest.skip("matplotlib not available in this environment")
