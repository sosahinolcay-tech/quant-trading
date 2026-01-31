from .event import OrderEvent, FillEvent
from typing import Literal, Optional, Any
from ..utils.numba_helpers import calculate_slippage_impact


class ExecutionModel:
    """Execution model with variable slippage and fee.

    - LIMIT orders are added to the `OrderBook` and not immediately filled.
    - MARKET-style fills (or fills produced by `OrderBook.process_trade`) should be
      converted to `FillEvent` instances using `fill_from_book` which applies
      slippage based on order size relative to liquidity and a simple fee.
    """

    def __init__(
        self,
        latency_ms: float = 0.0,
        fee: float = 0.0,
        slippage_coeff: float = 0.0,
        half_spread_bps: float = 0.0,
        impact_coeff: float = 0.0,
    ):
        self.latency_ms = latency_ms
        self.fee = float(fee)
        # slippage coefficient governs impact: fraction of price * (qty / liquidity)
        self.slippage_coeff = float(slippage_coeff)
        # fixed half-spread in basis points for marketable fills
        self.half_spread_bps = float(half_spread_bps)
        # additional impact coefficient applied to qty/liquidity
        self.impact_coeff = float(impact_coeff)

    def simulate_fill(self, order: OrderEvent, order_book: Optional[Any] = None) -> Optional[FillEvent]:
        # If it's a limit order, add to the book and return None (resting)
        if order.order_type == "LIMIT":
            if order_book is None:
                raise ValueError("OrderBook required to add limit orders")
            order_book.add_limit_order(order)
            return None

        # MARKET orders: immediate fill at top-of-book price (not used heavily in demo)
        # We'll compute a simple slippage assuming liquidity equals top-of-book depth.
        # For now, treat like immediate fill at order.price with slippage
        price = float(order.price)
        qty = float(order.quantity)
        liquidity = 1.0
        if order_book is not None:
            # liquidity available on the opposite side of the aggressor
            opp_side = "SELL" if order.side == "BUY" else "BUY"
            liquidity = order_book.liquidity_at(price, opp_side)
            liquidity = liquidity if liquidity > 0 else 1.0
        sign = 1.0 if order.side == "BUY" else -1.0
        spread = price * (self.half_spread_bps / 10000.0)
        # Use numba-accelerated slippage calculation with fallback
        try:
            slippage = calculate_slippage_impact(qty, liquidity, price, self.slippage_coeff)
        except Exception:
            # Fallback to simple calculation
            if liquidity <= 0:
                liquidity = 1.0
            slippage = self.slippage_coeff * (qty / liquidity) * price
        impact = self.impact_coeff * (qty / max(liquidity, 1e-9)) * price
        executed_price = price + sign * (spread + slippage + impact)
        fee_amount = float(self.fee) * abs(qty * executed_price)
        return FillEvent(
            order_id=order.order_id,
            timestamp=order.timestamp + self.latency_ms / 1000.0,
            symbol=order.symbol,
            side=order.side,
            price=executed_price,
            quantity=order.quantity,
            fee=fee_amount,
        )

    def fill_from_book(
        self,
        order_id: str,
        side: Literal["BUY", "SELL"],
        price: float,
        quantity: float,
        timestamp: float,
        order_book: Optional[Any] = None,
    ) -> FillEvent:
        """Create a FillEvent for a resting order matched by a market trade.

        Uses the order_book to infer liquidity at the price and apply slippage
        proportional to quantity / liquidity.
        """
        qty = float(quantity)
        p = float(price)
        liquidity = 1.0
        if order_book is not None:
            opp_side = "SELL" if side == "BUY" else "BUY"
            liquidity = order_book.liquidity_at(p, opp_side)
            liquidity = liquidity if liquidity > 0 else 1.0
        sign = 1.0 if side == "BUY" else -1.0
        spread = p * (self.half_spread_bps / 10000.0)
        # Use numba-accelerated slippage calculation with fallback
        try:
            slippage = calculate_slippage_impact(qty, liquidity, p, self.slippage_coeff)
        except Exception:
            # Fallback to simple calculation
            if liquidity <= 0:
                liquidity = 1.0
            slippage = self.slippage_coeff * (qty / liquidity) * p
        impact = self.impact_coeff * (qty / max(liquidity, 1e-9)) * p
        executed_price = p + sign * (spread + slippage + impact)
        fee_amount = float(self.fee) * abs(qty * executed_price)
        return FillEvent(
            order_id=order_id,
            timestamp=timestamp + self.latency_ms / 1000.0,
            symbol=None,
            side=side,
            price=executed_price,
            quantity=qty,
            fee=fee_amount,
        )
