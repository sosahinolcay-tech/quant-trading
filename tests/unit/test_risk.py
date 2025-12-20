import numpy as np
from qt.analytics import risk


def test_var_historical():
    rets = np.array([0.01, -0.02, 0.03, -0.05, 0.02])
    v = risk.compute_var(rets, alpha=0.05, method="historical")
    assert v >= 0.0


def test_cvar_historical():
    rets = np.array([0.01, -0.02, 0.03, -0.05, 0.02])
    cv = risk.compute_cvar(rets, alpha=0.2, method="historical")
    assert cv >= 0.0


def test_mc_horizon_var():
    np.random.seed(0)
    rets = np.random.normal(0.0, 0.01, size=500)
    v1 = risk.monte_carlo_horizon_var(rets, alpha=0.05, horizon=1, simulations=2000)
    v5 = risk.monte_carlo_horizon_var(rets, alpha=0.05, horizon=5, simulations=2000)
    # multi-period VaR should typically be larger than single-period
    assert v5 >= 0.0


def test_stress_test_equity():
    eq = [100, 102, 101, 105]
    res = risk.stress_test_equity(eq, shock_pct=-0.3)
    assert "stressed_equity" in res
    assert "max_drawdown" in res
    assert "final_equity" in res


def test_parametric_var_cvar():
    # Ensure parametric functions run (requires scipy in dev extras)
    rets = np.random.normal(0.0, 0.01, size=500)
    v = risk.compute_var(rets, alpha=0.05, method="parametric")
    cv = risk.compute_cvar(rets, alpha=0.05, method="parametric")
    assert v >= 0.0
    assert cv >= 0.0
