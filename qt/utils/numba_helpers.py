try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:
    def njit(func=None, **kwargs):
        # fallback no-op decorator
        def _decorator(f):
            return f
        if func is None:
            return _decorator
        return _decorator(func)
    NUMBA_AVAILABLE = False


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


@njit
def compute_liquidity_sum(quantities):
    """Fast sum of quantities for order book liquidity calculation.
    
    Args:
        quantities: Array-like of quantity values (must be numpy array)
    
    Returns:
        Sum of all quantities
    """
    total = 0.0
    n = len(quantities)
    for i in range(n):
        total += quantities[i]
    return total


@njit
def find_best_price_level(price_levels, reverse):
    """Find best bid/ask price level efficiently.
    
    Args:
        price_levels: Array-like of price levels (must be numpy array)
        reverse: If True (1), find maximum (bids), else find minimum (asks)
    
    Returns:
        Best price level or 0.0 if empty
    """
    n = len(price_levels)
    if n == 0:
        return 0.0
    best = price_levels[0]
    for i in range(1, n):
        price = price_levels[i]
        if reverse:
            if price > best:
                best = price
        else:
            if price < best:
                best = price
    return best


@njit
def calculate_slippage_impact(quantity, liquidity, price, slippage_coeff):
    """Calculate slippage impact for order execution.
    
    Args:
        quantity: Order quantity
        liquidity: Available liquidity
        price: Order price
        slippage_coeff: Slippage coefficient
    
    Returns:
        Slippage amount
    """
    if liquidity <= 0:
        liquidity = 1.0
    return slippage_coeff * (quantity / liquidity) * price
