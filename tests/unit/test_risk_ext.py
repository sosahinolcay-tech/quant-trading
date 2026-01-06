import numpy as np
from qt.analytics import risk_ext


def test_multi_asset_mc_var_shapes():
    np.random.seed(1)
    # 3 assets, 500 days
    rets = np.random.normal(0, 0.01, size=(500, 3))
    weights = np.array([0.5, 0.3, 0.2])
    v = risk_ext.multi_asset_monte_carlo_var(rets, weights, portfolio_value=100.0, simulations=1000)
    assert v >= 0.0


def test_bootstrap_var_basic():
    np.random.seed(2)
    rets = np.random.normal(0, 0.02, size=200)
    v = risk_ext.bootstrap_var(rets, alpha=0.05, horizon=5, simulations=2000)
    assert v >= 0.0


def test_apply_scenario_portfolio():
    weights = [0.6, 0.4]
    init = 100.0
    # simple two-step scenario where first asset drops 10% then recovers
    scenario = [[-0.1, 0.0], [0.05, -0.02]]
    out = risk_ext.apply_historical_scenario_to_portfolio(weights, init, None, scenario)
    assert 'stressed_equity' in out
    assert out['final_equity'] > 0


def test_garch_sim_and_var():
    np.random.seed(3)
    rets = np.random.normal(0, 0.01, size=500)
    sims = risk_ext.simulate_garch_returns(rets, horizon=10, simulations=500)
    assert sims.shape[0] == 500
    v = risk_ext.garch_var(rets, horizon=10, simulations=500)
    assert v >= 0.0
