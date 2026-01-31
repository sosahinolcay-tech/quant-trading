"""Extended risk utilities for Week 5: multi-asset MC, bootstrap, scenario replay,
and a lightweight GARCH-like simulator.
"""

from typing import Any, Dict, Sequence

import numpy as np
from typing import List


def multi_asset_monte_carlo_var(
    returns_matrix, weights, portfolio_value: float = 1.0, alpha: float = 0.05, horizon: int = 1, simulations: int = 10000
) -> float:
    """Multi-asset Monte Carlo VaR for a portfolio defined by asset weights.

    Parameters
    - returns_matrix: 2D array-like with shape (T, N) where each column is an asset return series
    - weights: 1D array-like of length N containing portfolio weights (summing to 1 if using weights)
    - portfolio_value: scalar, starting portfolio value in currency units
    - alpha: tail probability
    - horizon: number of periods to aggregate
    - simulations: number of Monte Carlo paths

    Returns the positive VaR value expressed in the same units as `portfolio_value`.
    """
    rets = np.asarray(returns_matrix, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if rets.ndim != 2:
        raise ValueError("returns_matrix must be 2D (T, N)")
    T, N = rets.shape
    if weights.shape[0] != N:
        raise ValueError("weights length must match number of assets (columns in returns_matrix)")

    if T < 2:
        return 0.0

    mu = np.mean(rets, axis=0)
    cov = np.cov(rets, rowvar=False)

    # Validate covariance matrix is positive semi-definite
    if not np.all(np.linalg.eigvals(cov) >= -1e-10):
        # If not PSD, make it PSD by adding small regularization
        cov = cov + np.eye(N) * 1e-10

    # draw sims x horizon x N multivariate normals
    sims = np.random.multivariate_normal(mean=mu, cov=cov, size=(simulations, horizon))
    # cumulative returns per sim per asset (sum across horizon)
    cumrets = np.sum(sims, axis=1)  # shape (simulations, N)
    # portfolio returns per simulation
    port_rets = cumrets.dot(weights)
    var = -np.quantile(port_rets, alpha)
    return float(var * portfolio_value)


def bootstrap_var(returns, alpha: float = 0.05, horizon: int = 1, simulations: int = 10000) -> float:
    """Estimate multi-period VaR by bootstrap resampling historical returns (with replacement).

    This avoids parametric assumptions and is useful for heavy-tailed data.
    """
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0 or horizon < 1:
        return 0.0

    sims = np.zeros(simulations)
    n = rets.shape[0]
    for i in range(simulations):
        idx = np.random.randint(0, n, size=horizon)
        sims[i] = np.sum(rets[idx])
    var = -np.quantile(sims, alpha)
    return float(var)


def apply_historical_scenario_to_portfolio(
    weights: Sequence[float],
    initial_portfolio_value: float,
    returns_matrix: Sequence[Sequence[float]],
    scenario_returns: Sequence[Sequence[float]],
) -> Dict[str, Any]:
    """Apply a multi-period historical scenario (sequence of returns) to a weighted portfolio.

    - `weights`: portfolio weights per asset (length N)
    - `returns_matrix`: historical returns used for reference (not strictly required, kept for consistency)
    - `scenario_returns`: 2D array-like with shape (horizon, N) of scenario returns to apply

    Returns a dict with stressed equity path, final equity and max drawdown.
    """
    scen = np.asarray(scenario_returns, dtype=float)
    if scen.ndim == 1:
        # single-period vector -> make it a 1 x N array
        scen = scen.reshape(1, -1)
    horizon, N = scen.shape
    w = np.asarray(weights, dtype=float)
    if w.shape[0] != N:
        raise ValueError("weights length must match scenario asset dimension")

    equity_list: List[float] = [float(initial_portfolio_value)]
    for t in range(horizon):
        port_ret = float(np.dot(scen[t, :], w))
        equity_list.append(equity_list[-1] * (1.0 + port_ret))
    equity: np.ndarray = np.array(equity_list, dtype=float)
    hwm = np.maximum.accumulate(equity)
    hwm = np.maximum(hwm, 1e-10)  # Prevent division by zero
    drawdown = (equity - hwm) / hwm
    max_dd = float(np.min(drawdown)) if drawdown.size > 0 else 0.0
    return {"stressed_equity": equity.tolist(), "max_drawdown": max_dd, "final_equity": float(equity[-1])}


def simulate_garch_returns(
    returns, horizon: int = 1, simulations: int = 10000, omega: float = 1e-6, alpha_g: float = 0.05, beta: float = 0.9
) -> np.ndarray:
    """Simulate horizon returns using a simple GARCH(1,1)-like recursion for variance.

    This is a lightweight, approximate simulator that uses user-provided GARCH
    parameters or sensible defaults. It returns an array of simulated cumulative
    returns (length `simulations`) for the horizon.
    """
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0 or horizon < 1:
        return np.zeros(simulations)

    # initialize variance from sample variance
    sigma2 = float(np.var(rets, ddof=1))

    sims = np.zeros((simulations, horizon), dtype=float)
    for t in range(horizon):
        eps = np.random.normal(loc=0.0, scale=np.sqrt(sigma2), size=simulations)
        sims[:, t] = eps
        # update sigma2 using average of eps^2 as a proxy for realized variance
        sigma2 = omega + alpha_g * float(np.mean(eps**2)) + beta * sigma2

    cumrets = np.sum(sims, axis=1)
    return cumrets


def garch_var(
    returns,
    alpha: float = 0.05,
    horizon: int = 1,
    simulations: int = 10000,
    omega: float = 1e-6,
    alpha_g: float = 0.05,
    beta: float = 0.9,
) -> float:
    """Estimate VaR using the GARCH-like simulator above."""
    sims = simulate_garch_returns(returns, horizon=horizon, simulations=simulations, omega=omega, alpha_g=alpha_g, beta=beta)
    var = -np.quantile(sims, alpha)
    return float(var)
