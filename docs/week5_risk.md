# Week 5 — Risk Analytics (VaR, CVaR, Stress Testing)

This document summarizes the Week 5 changes: tail-risk metrics and simple
stress-testing utilities added to the `qt` analytics package.

Overview
--------
- `qt.analytics.risk` provides:
  - `compute_var(returns, alpha, method, simulations)` — Value-at-Risk
    estimation supporting `historical`, `parametric` (normal) and `mc`.
  - `compute_cvar(returns, alpha, method, simulations)` — Conditional VaR
    (Expected Shortfall) with the same method options.
  - `monte_carlo_horizon_var(returns, alpha, horizon, simulations)` —
    multi-period Monte Carlo VaR for short horizons (iid normal approx).
  - `stress_test_equity(equity_curve, shock_pct)` — apply a simple shock
    (e.g. -0.3 for -30%) to the last return and return stressed equity
    plus drawdown statistics.

Assumptions and Limitations
---------------------------
- Parametric methods assume returns are approximately normal — this is a
  simplification and may underestimate tail risk for heavy-tailed returns.
- The Monte Carlo implementations use iid normal sampling for simplicity.
  For multi-asset or heteroskedastic returns, extend to bootstrap
  historical returns or use a fitted multivariate model.
- `stress_test_equity` implements a basic single-shock scenario. A fuller
  stress framework should support historical scenario replay, multi-factor
  shocks, and path-dependent P&L calculations.

Usage Examples
--------------
```python
from qt.analytics import risk
rets = [0.01, -0.02, 0.03, -0.05, 0.02]
var95 = risk.compute_var(rets, alpha=0.05, method='historical')
cvar95 = risk.compute_cvar(rets, alpha=0.05, method='historical')
mc5d = risk.monte_carlo_horizon_var(rets, alpha=0.05, horizon=5, simulations=5000)

stressed = risk.stress_test_equity([100, 102, 101, 105], shock_pct=-0.3)
```

Next steps
----------
- Expand Monte Carlo to multi-asset portfolio P&L simulation using positions
- Add historical scenario library and multi-factor shocks
- Integrate bootstrap sampling and GARCH-like innovations for heteroskedasticity

Tests
-----
Unit tests are in `tests/unit/test_risk.py` and cover historical, MC and
stress test behaviors. CI will install `dev` extras (including `scipy`) so
parametric tests run in the pipeline.
