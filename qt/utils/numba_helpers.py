try:
    from numba import njit
except Exception:
    def njit(func=None, **kwargs):
        # fallback no-op decorator
        def _decorator(f):
            return f
        if func is None:
            return _decorator
        return _decorator(func)


@njit
def simple_volatility(returns):
    # note: numba-compiled version if available
    s = 0.0
    n = len(returns)
    if n == 0:
        return 0.0
    mean = 0.0
    for r in returns:
        mean += r
    mean /= n
    for r in returns:
        s += (r - mean) ** 2
    var = s / (n - 1) if n > 1 else 0.0
    return (var ** 0.5) * (252 ** 0.5)
