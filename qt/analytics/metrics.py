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
        w = rets[i - window + 1 : i + 1]
        shs[i] = compute_sharpe(w, annualization=annualization)
    # pad to match equity_curve length (equity length = returns+1)
    padded = np.full(eq.shape, np.nan)
    padded[1:] = shs
    return padded


def rolling_volatility(returns, window: int = 20, annualization: float = TRADING_DAYS_PER_YEAR):
    rets = np.asarray(returns, dtype=float)
    if rets.size < window:
        return np.full(rets.shape, np.nan)
    vols = np.full(rets.shape, np.nan)
    for i in range(window - 1, len(rets)):
        w = rets[i - window + 1 : i + 1]
        vols[i] = np.std(w, ddof=1) * np.sqrt(annualization)
    return vols


def compute_return_stats(returns):
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0:
        return {"mean": 0.0, "std": 0.0, "skew": 0.0, "kurtosis": 0.0}
    mean = np.mean(rets)
    std = np.std(rets, ddof=1)
    centered = rets - mean
    denom = np.maximum(std, EPSILON) ** 3
    skew = np.mean(centered**3) / denom
    kurt = np.mean(centered**4) / np.maximum(std, EPSILON) ** 4 - 3.0
    return {"mean": float(mean), "std": float(std), "skew": float(skew), "kurtosis": float(kurt)}


def compute_cagr(equity_curve, annualization: float = TRADING_DAYS_PER_YEAR) -> float:
    eq = np.asarray(equity_curve, dtype=float)
    if eq.size < 2:
        return 0.0
    total_return = eq[-1] / np.maximum(eq[0], EPSILON)
    years = (eq.size - 1) / annualization
    if years <= 0:
        return 0.0
    return float(total_return ** (1.0 / years) - 1.0)


def compute_sortino(returns, annualization: float = TRADING_DAYS_PER_YEAR) -> float:
    rets = np.asarray(returns, dtype=float)
    if rets.size == 0:
        return 0.0
    downside = rets[rets < 0]
    if downside.size == 0:
        return 0.0
    downside_std = np.std(downside, ddof=1)
    if downside_std < EPSILON:
        return 0.0
    return float(np.mean(rets) / downside_std * np.sqrt(annualization))


def compute_calmar(equity_curve, annualization: float = TRADING_DAYS_PER_YEAR) -> float:
    cagr = compute_cagr(equity_curve, annualization=annualization)
    dd = compute_drawdown(equity_curve)
    max_dd = abs(dd.get("max_drawdown", 0.0))
    if max_dd < EPSILON:
        return 0.0
    return float(cagr / max_dd)


def compute_drawdown_duration(equity_curve):
    eq = np.asarray(equity_curve, dtype=float)
    if eq.size == 0:
        return {"max_duration": 0, "avg_duration": 0.0}
    hwm = np.maximum.accumulate(eq)
    underwater = eq < hwm
    durations = []
    current = 0
    for flag in underwater:
        if flag:
            current += 1
        else:
            if current > 0:
                durations.append(current)
            current = 0
    if current > 0:
        durations.append(current)
    if not durations:
        return {"max_duration": 0, "avg_duration": 0.0}
    return {"max_duration": int(max(durations)), "avg_duration": float(np.mean(durations))}


def _safe_mpl_backend():
    try:
        import matplotlib

        if matplotlib.get_backend().lower() != "agg":
            matplotlib.use("Agg", force=True)
    except Exception:
        return


def plot_equity_curve(equity_curve, ax=None, title="Equity Curve", savepath=None):
    """Plot an equity curve using matplotlib. Returns the matplotlib Axes.

    If matplotlib is not available, raises ImportError.
    """
    _safe_mpl_backend()
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
    _safe_mpl_backend()
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
    _safe_mpl_backend()
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
