from typing import Dict, List, Tuple, Optional, Any


class Account:
    """Very small accounting module: track positions, cash, and mark-to-market equity history."""

    def __init__(self, initial_cash: float = 100000.0, fee: float = 0.0):
        self.cash = float(initial_cash)
        self.fee = float(fee)
        self.positions: Dict[str, float] = {}
        # equity history as list of (timestamp, equity)
        self.equity_history: List[Tuple[float, float]] = []

    def on_fill(self, fill):
        """Process a fill event and update account positions and cash.
        
        Args:
            fill: FillEvent with attributes: order_id, timestamp, symbol, side, price, quantity, fee
        
        Raises:
            AttributeError: If fill is missing required attributes
            ValueError: If price or quantity is invalid
        """
        # Validate fill has required attributes
        required_attrs = ['quantity', 'price', 'symbol', 'side']
        for attr in required_attrs:
            if not hasattr(fill, attr):
                raise AttributeError(f"Fill object missing required attribute: {attr}")
        
        qty = float(fill.quantity)
        price = float(fill.price)
        symbol = fill.symbol
        side = fill.side
        
        # Validate inputs
        if price <= 0:
            raise ValueError(f"Invalid fill price: {price}. Price must be positive.")
        if qty <= 0:
            raise ValueError(f"Invalid fill quantity: {qty}. Quantity must be positive.")
        # buy decreases cash, increases position; sell increases cash, decreases position
        if side == "BUY":
            self.positions[symbol] = self.positions.get(symbol, 0.0) + qty
            self.cash -= qty * price
        else:
            self.positions[symbol] = self.positions.get(symbol, 0.0) - qty
            self.cash += qty * price
        # subtract fees: prefer fee reported by fill, else fall back to account-level fee
        fee_amt = 0.0
        if hasattr(fill, 'fee') and fill.fee:
            fee_amt = float(fill.fee)
        elif self.fee:
            fee_amt = abs(qty * price) * float(self.fee)
        if fee_amt:
            self.cash -= fee_amt

    def mark_to_market(self, timestamp: float, last_prices: Dict[str, float]) -> float:
        # compute equity = cash + sum(pos * last_price)
        equity = float(self.cash)
        for sym, pos in self.positions.items():
            price = last_prices.get(sym)
            if price is not None:
                equity += pos * float(price)
        self.equity_history.append((float(timestamp), equity))
        return equity

    def get_equity_curve(self) -> List[float]:
        """Get equity curve as a list of equity values.
        
        Returns:
            List of equity values (one per timestamp in equity_history)
        """
        return [e for (_, e) in self.equity_history]
