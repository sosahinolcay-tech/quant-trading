import numpy as np


def compute_returns(equity_curve):
    # equity_curve: list or np.array of portfolio values
    eq = np.array(equity_curve)
    returns = eq[1:] / eq[:-1] - 1.0
    return returns


def compute_sharpe(returns, annualization=252.0):
    if len(returns) == 0:
        return 0.0
    sr = np.mean(returns) / (np.std(returns, ddof=1) + 1e-9) * np.sqrt(annualization)
    return float(sr)


def compute_drawdown(equity_curve):
    eq = np.array(equity_curve, dtype=float)
    hwm = np.maximum.accumulate(eq)
    drawdown = (eq - hwm) / hwm
    max_dd = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    return {
        "drawdown_series": drawdown.tolist(),
        "max_drawdown": max_dd,
    }


def rolling_sharpe(equity_curve, window=20, annualization=252.0):
    eq = np.array(equity_curve)
    rets = compute_returns(eq)
    if len(rets) < window:
        return []
    rolls = []
    for i in range(len(rets) - window + 1):
        w = rets[i:i+window]
        rolls.append(compute_sharpe(w, annualization=annualization))
    return rolls
