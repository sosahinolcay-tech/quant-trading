from typing import List, Tuple, Dict, Optional, Union, Any
from collections import defaultdict, deque
import numpy as np
from ..utils.numba_helpers import compute_liquidity_sum, find_best_price_level


class OrderBook:
    """Simple limit order book with price levels and FIFO queues per level.

    This is not a production-grade matching engine but provides basic
    resting-limit order behavior: limit orders are stored at price levels
    and only filled when a market trade hits that price level.
    """

    def __init__(self):
        # price -> deque of orders (order dicts)
        self.bids: Dict[float, deque] = defaultdict(deque)
        self.asks: Dict[float, deque] = defaultdict(deque)
        # maintain sorted lists of price levels for quick best bid/ask
        self.bid_levels: List[float] = []
        self.ask_levels: List[float] = []
        self.last_price = 0.0

    def update_from_snapshot(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        # initialize top-of-book from snapshot
        self.bids.clear()
        self.asks.clear()
        self.bid_levels.clear()
        self.ask_levels.clear()
        for p, s in bids:
            if p <= 0 or s <= 0:
                continue  # Skip invalid orders
            self.bid_levels.append(p)
            # seed with a synthetic liquidity order representing displayed depth
            self.bids[p].append({'order_id': f'snap-bid-{int(p*100)}', 'price': p, 'quantity': s, 'side': 'BUY'})
        for p, s in asks:
            if p <= 0 or s <= 0:
                continue  # Skip invalid orders
            self.ask_levels.append(p)
            self.asks[p].append({'order_id': f'snap-ask-{int(p*100)}', 'price': p, 'quantity': s, 'side': 'SELL'})
        self.bid_levels.sort(reverse=True)
        self.ask_levels.sort()

    def apply_trade(self, price: float, size: float):
        # update last traded price
        self.last_price = price

    def mid_price(self) -> float:
        """Calculate mid price from best bid/ask levels.
        
        Uses optimized numba function if available for better performance.
        Falls back to simple list operations if numba fails.
        """
        if self.bid_levels and self.ask_levels:
            try:
                # Try numba-accelerated version
                bid_array = np.array(self.bid_levels, dtype=np.float64)
                ask_array = np.array(self.ask_levels, dtype=np.float64)
                b = find_best_price_level(bid_array, True)
                a = find_best_price_level(ask_array, False)
                if b > 0 and a > 0:
                    return (b + a) / 2.0
            except Exception:
                # Fallback to simple Python operations
                b = max(self.bid_levels) if self.bid_levels else 0.0
                a = min(self.ask_levels) if self.ask_levels else 0.0
                if b > 0 and a > 0:
                    return (b + a) / 2.0
        return self.last_price if self.last_price > 0 else 0.0

    def _insert_level(self, levels: List[float], price: float, reverse: bool = False):
        if price in levels:
            return
        levels.append(price)
        levels.sort(reverse=reverse)

    def add_limit_order(self, order: Union[str, Any], price: Optional[float] = None, qty: Optional[float] = None) -> str:
        """Add a limit order to the book.

        Supports two call styles for backward compatibility:
        - add_limit_order(order_event)
        - add_limit_order(side, price=..., qty=...)

        Returns the order_id.
        
        Raises:
            ValueError: If price or quantity is invalid (<= 0).
        """
        # backward compatible call: add_limit_order('BUY', price=100.0, qty=5)
        if isinstance(order, str):
            side = order
            price = float(price) if price is not None else 0.0
            qty = float(qty) if qty is not None else 0.0
            # Validate inputs
            if price <= 0:
                raise ValueError(f"Invalid price: {price}. Price must be positive.")
            if qty <= 0:
                raise ValueError(f"Invalid quantity: {qty}. Quantity must be positive.")
            # synthesize an order id
            order_id = f"legacy-{int(price*100)}-{int(qty)}"
            order_dict = {'order_id': order_id, 'price': price, 'quantity': qty, 'side': side, 'symbol': None, 'timestamp': 0.0}
        else:
            price = float(order.price)
            qty = float(order.quantity)
            # Validate inputs
            if price <= 0:
                raise ValueError(f"Invalid price: {price}. Price must be positive.")
            if qty <= 0:
                raise ValueError(f"Invalid quantity: {qty}. Quantity must be positive.")
            side = order.side
            order_dict = {
                'order_id': order.order_id,
                'price': price,
                'quantity': qty,
                'side': side,
                'symbol': order.symbol,
                'timestamp': order.timestamp,
            }
        if side == 'BUY':
            # bids: descending
            self.bids[price].append(order_dict)
            self._insert_level(self.bid_levels, price, reverse=True)
        else:
            # asks: ascending
            self.asks[price].append(order_dict)
            self._insert_level(self.ask_levels, price, reverse=False)
        order_id: str = str(order_dict['order_id'])
        return order_id

    def liquidity_at(self, price: float, side: str) -> float:
        """Calculate total liquidity at a specific price level.
        
        Uses optimized numba function for better performance.
        Falls back to simple sum if numba fails.
        """
        lvl = self.bids if side == 'BUY' else self.asks
        orders: List[Dict[str, Any]] = lvl.get(price, [])
        if not orders:
            return 0.0
        try:
            # Try numba-accelerated version
            quantities = np.array([o['quantity'] for o in orders], dtype=np.float64)
            return compute_liquidity_sum(quantities)
        except Exception:
            # Fallback to simple Python sum
            return sum(o['quantity'] for o in orders)

    def process_trade(self, price: float, size: float):
        """Process an incoming market trade at `price` for total `size`.

        This will match against resting limit orders at that price level
        (FIFO) and return a list of fill dicts with keys: order_id, price, quantity, side, symbol.
        """
        fills = []
        remaining = float(size)

        # check asks at price (sell liquidity resting) -> buy market hit
        if price in self.asks and remaining > 0:
            qdeque = self.asks[price]
            while qdeque and remaining > 0:
                o = qdeque[0]
                take = min(o['quantity'], remaining)
                fills.append({'order_id': o['order_id'], 'price': price, 'quantity': take, 'side': 'SELL', 'symbol': o.get('symbol')})
                o['quantity'] -= take
                remaining -= take
                if o['quantity'] <= 0:
                    qdeque.popleft()
            if not qdeque:
                # remove level
                try:
                    self.ask_levels.remove(price)
                except ValueError:
                    pass

        # check bids at price (buy liquidity resting) -> sell market hit
        if price in self.bids and remaining > 0:
            qdeque = self.bids[price]
            while qdeque and remaining > 0:
                o = qdeque[0]
                take = min(o['quantity'], remaining)
                fills.append({'order_id': o['order_id'], 'price': price, 'quantity': take, 'side': 'BUY', 'symbol': o.get('symbol')})
                o['quantity'] -= take
                remaining -= take
                if o['quantity'] <= 0:
                    qdeque.popleft()
            if not qdeque:
                try:
                    self.bid_levels.remove(price)
                except ValueError:
                    pass

        return fills
