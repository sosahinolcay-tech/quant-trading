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
    """Return a rolling Sharpe series aligned to the input equity_curve.

    This returns a numpy array with the same length as `equity_curve`.
    Values before the first full window are padded with np.nan so plotting
    or alignment with timestamps is straightforward.
    """
    eq = np.array(equity_curve, dtype=float)
    if eq.size < 2:
        return np.full(eq.shape, np.nan)
    rets = compute_returns(eq)
    n = len(rets)
    if n < window:
        # not enough returns to compute a single window
        return np.full(eq.shape, np.nan)
    shs = np.full(n, np.nan)
    for i in range(window - 1, n):
        w = rets[i - window + 1:i + 1]
        shs[i] = compute_sharpe(w, annualization=annualization)
    # pad to match equity_curve length (equity length = returns+1)
    padded = np.full(eq.shape, np.nan)
    padded[1:] = shs
    return padded


def plot_equity_curve(equity_curve, ax=None, title="Equity Curve", savepath=None):
    """Plot an equity curve using matplotlib. Returns the matplotlib Axes.

    If matplotlib is not available, raises ImportError.
    """
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("matplotlib required for plotting") from e

    eq = np.array(equity_curve, dtype=float)
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(eq, label="Equity")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Equity")
    ax.grid(True)
    ax.legend()
    if savepath:
        fig = ax.get_figure()
        fig.savefig(savepath, bbox_inches="tight")
    return ax


def plot_drawdown(equity_curve, ax=None, title="Drawdown", savepath=None):
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("matplotlib required for plotting") from e

    dd = compute_drawdown(equity_curve)
    series = np.array(dd.get("drawdown_series", []), dtype=float)
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(series, label="Drawdown")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Drawdown")
    ax.grid(True)
    ax.legend()
    if savepath:
        fig = ax.get_figure()
        fig.savefig(savepath, bbox_inches="tight")
    return ax


def plot_rolling_sharpe(equity_curve, window=20, ax=None, title="Rolling Sharpe", savepath=None):
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("matplotlib required for plotting") from e

    series = rolling_sharpe(equity_curve, window=window)
    if ax is None:
        fig, ax = plt.subplots()
    ax.plot(series, label=f"Rolling Sharpe (w={window})")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel("Sharpe")
    ax.grid(True)
    ax.legend()
    if savepath:
        fig = ax.get_figure()
        fig.savefig(savepath, bbox_inches="tight")
    return ax
