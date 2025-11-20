from typing import Dict, List, Tuple


class Account:
    """Very small accounting module: track positions, cash, and mark-to-market equity history."""

    def __init__(self, initial_cash: float = 100000.0, fee: float = 0.0):
        self.cash = float(initial_cash)
        self.fee = float(fee)
        self.positions: Dict[str, float] = {}
        # equity history as list of (timestamp, equity)
        self.equity_history: List[Tuple[float, float]] = []

    def on_fill(self, fill):
        # fill: must have attributes order_id, timestamp, symbol, side, price, quantity
        qty = float(fill.quantity)
        price = float(fill.price)
        symbol = fill.symbol
        side = fill.side
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

    def mark_to_market(self, timestamp: float, last_prices: Dict[str, float]):
        # compute equity = cash + sum(pos * last_price)
        equity = float(self.cash)
        for sym, pos in self.positions.items():
            price = last_prices.get(sym)
            if price is not None:
                equity += pos * float(price)
        self.equity_history.append((float(timestamp), equity))
        return equity

    def get_equity_curve(self):
        return [e for (_, e) in self.equity_history]
