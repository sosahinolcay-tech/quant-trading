from .event import OrderEvent, FillEvent


class ExecutionModel:
    """Simple deterministic execution model: immediate fills at given price."""

    def __init__(self, latency_ms: float = 0.0, fee: float = 0.0, slippage_coeff: float = 0.0):
        self.latency_ms = latency_ms
        self.fee = fee
        # slippage coefficient as fraction of price per unit qty
        self.slippage_coeff = slippage_coeff

    def simulate_fill(self, order: OrderEvent) -> FillEvent:
        # deterministic immediate fill at order price
        # deterministic immediate fill at order price with simple slippage and fee
        sign = 1.0 if order.side == "BUY" else -1.0
        slippage = self.slippage_coeff * float(order.quantity) * float(order.price)
        executed_price = float(order.price) + sign * slippage
        fee_amount = float(self.fee) * abs(float(order.quantity) * executed_price)
        return FillEvent(
            order_id=order.order_id,
            timestamp=order.timestamp + self.latency_ms / 1000.0,
            symbol=order.symbol,
            side=order.side,
            price=executed_price,
            quantity=order.quantity,
            fee=fee_amount,
        )
