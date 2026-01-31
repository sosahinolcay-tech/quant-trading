"""Risk analytics helpers: VaR, CVaR and simple stress testing.

These utilities are lightweight and intended for use in analysis pipelines
and dashboards. They support historical, parametric (normal) and Monte Carlo
methods for tail-risk estimation.
"""

from typing import Any, Dict
import numpy as np
from typing import List


def compute_var(returns, alpha: float = 0.05, method: str = "historical", simulations: int = 10000) -> float:
    """Compute Value-at-Risk (VaR) for a returns series.

    Parameters
    - returns: 1D array-like of returns (decimal, e.g. 0.01 = 1%)
    - alpha: tail probability (e.g. 0.05 for 95% VaR)
    - method: "historical" | "parametric" | "mc"
    - simulations: number of MC sims when method == "mc"

    Returns the positive VaR number (loss expressed as positive value).
    """
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0:
        return 0.0

    if method == "historical":
        # historical empirical quantile
        var = -np.quantile(rets, alpha)
        return float(var)

    if method == "parametric":
        mu = np.mean(rets)
        sigma = np.std(rets, ddof=1)
        try:
            from scipy.stats import norm
        except Exception:
            raise ImportError("scipy required for parametric VaR")

        z = norm.ppf(alpha)
        var = -(mu + sigma * z)
        return float(var)

    if method == "mc":
        mu = np.mean(rets)
        sigma = np.std(rets, ddof=1)
        sims = np.random.normal(loc=mu, scale=sigma, size=simulations)
        var = -np.quantile(sims, alpha)
        return float(var)

    raise ValueError(f"Unknown method for VaR: {method}")


def compute_cvar(returns, alpha: float = 0.05, method: str = "historical", simulations: int = 10000) -> float:
    """Compute Conditional VaR (Expected Shortfall) at level alpha.

    Returns positive expected loss in the tail.
    """
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0:
        return 0.0

    if method == "historical":
        thresh = np.quantile(rets, alpha)
        tail = rets[rets <= thresh]
        if tail.size == 0:
            return 0.0
        return float(-np.mean(tail))

    if method == "parametric":
        mu = np.mean(rets)
        sigma = np.std(rets, ddof=1)
        try:
            from scipy.stats import norm
        except Exception:
            raise ImportError("scipy required for parametric CVaR")

        z = norm.ppf(alpha)
        pdf = norm.pdf(z)
        cvar = -(mu - sigma * pdf / alpha)
        return float(cvar)

    if method == "mc":
        mu = np.mean(rets)
        sigma = np.std(rets, ddof=1)
        sims = np.random.normal(loc=mu, scale=sigma, size=simulations)
        thresh = np.quantile(sims, alpha)
        tail = sims[sims <= thresh]
        if tail.size == 0:
            return 0.0
        return float(-np.mean(tail))

    raise ValueError(f"Unknown method for CVaR: {method}")


def monte_carlo_horizon_var(returns, alpha: float = 0.05, horizon: int = 1, simulations: int = 10000) -> float:
    """Estimate multi-period VaR by Monte Carlo assuming iid returns (normal approx).

    - returns: historical returns series
    - horizon: number of periods to aggregate (e.g., days)
    - simulations: number of MC paths
    Returns positive VaR (loss) over the horizon.
    """
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0 or horizon < 1:
        return 0.0

    mu = np.mean(rets)
    sigma = np.std(rets, ddof=1)
    # simulate horizon cumulative returns assuming iid normal
    sims = np.random.normal(loc=mu, scale=sigma, size=(simulations, horizon))
    # cumulative log-returns approximation: sum of returns
    cumrets = np.sum(sims, axis=1)
    # convert to simple returns over horizon roughly as (1+sum) for small returns
    # compute quantile
    var = -np.quantile(cumrets, alpha)
    return float(var)


def stress_test_equity(equity_curve, shock_pct: float = -0.3) -> Dict[str, Any]:
    """Apply a simple stress shock to an equity curve and return results.

    - `shock_pct` is applied additively to the most recent return (e.g. -0.3 = -30% shock)
    Returns dictionary with keys: 'stressed_equity', 'max_drawdown', 'final_equity'
    """
    eq = np.asarray(equity_curve, dtype=float)
    if eq.size == 0:
        return {"stressed_equity": [], "max_drawdown": 0.0, "final_equity": None}

    # compute returns and apply shock to the last return as a simple scenario
    eq_prev = np.maximum(eq[:-1], 1e-10)  # Prevent division by zero
    rets = eq[1:] / eq_prev - 1.0
    shocked_rets = rets.copy()
    if shocked_rets.size > 0:
        shocked_rets[-1] = shocked_rets[-1] + shock_pct

    stressed_list: List[float] = [eq[0]]
    for r in shocked_rets:
        stressed_list.append(stressed_list[-1] * (1.0 + r))
    stressed: np.ndarray = np.array(stressed_list, dtype=float)

    # compute drawdown
    hwm = np.maximum.accumulate(stressed)
    hwm = np.maximum(hwm, 1e-10)  # Prevent division by zero
    drawdown = (stressed - hwm) / hwm
    max_dd = float(np.min(drawdown)) if drawdown.size > 0 else 0.0

    return {"stressed_equity": stressed.tolist(), "max_drawdown": max_dd, "final_equity": float(stressed[-1])}
