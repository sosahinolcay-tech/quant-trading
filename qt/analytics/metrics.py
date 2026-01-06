import numpy as np

# Constants
EPSILON = 1e-9  # Small value to prevent division by zero
TRADING_DAYS_PER_YEAR = 252.0  # Standard trading days per year


def compute_returns(equity_curve):
    """Compute returns from equity curve.
    
    Args:
        equity_curve: Array-like of portfolio values
    
    Returns:
        Array of returns (one less element than input)
    """
    eq = np.array(equity_curve, dtype=float)
    if eq.size < 2:
        return np.array([], dtype=float)
    # Prevent division by zero
    eq_prev = np.maximum(eq[:-1], EPSILON)
    returns = eq[1:] / eq_prev - 1.0
    return returns


def compute_sharpe(returns, annualization: float = TRADING_DAYS_PER_YEAR) -> float:
    """Compute Sharpe ratio for a returns series.
    
    Args:
        returns: Array-like of returns
        annualization: Annualization factor (default: 252 trading days)
    
    Returns:
        Sharpe ratio as float
    """
    if len(returns) == 0:
        return 0.0
    std = np.std(returns, ddof=1)
    if std < EPSILON:
        return 0.0  # Avoid division by zero for constant returns
    sr = np.mean(returns) / std * np.sqrt(annualization)
    return float(sr)


def compute_drawdown(equity_curve):
    """Compute drawdown series and maximum drawdown.
    
    Args:
        equity_curve: Array-like of equity values
    
    Returns:
        Dictionary with 'drawdown_series' and 'max_drawdown' keys
    """
    eq = np.array(equity_curve, dtype=float)
    if eq.size == 0:
        return {"drawdown_series": [], "max_drawdown": 0.0}
    
    hwm = np.maximum.accumulate(eq)
    # Prevent division by zero - use epsilon for very small values
    hwm = np.maximum(hwm, EPSILON)
    drawdown = (eq - hwm) / hwm
    max_dd = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0
    return {
        "drawdown_series": drawdown.tolist(),
        "max_drawdown": max_dd,
    }


def rolling_sharpe(equity_curve, window: int = 20, annualization: float = TRADING_DAYS_PER_YEAR):
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
