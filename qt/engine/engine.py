from typing import List, Dict, Any, Optional
from ..engine.event import MarketEvent, FillEvent
from .order_book import OrderBook
from .execution import ExecutionModel
from ..risk.accounting import Account
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_SPREAD_PCT = 0.01  # 1% default spread


class SimulationEngine:
    def __init__(self, execution_fee: float = 0.0, slippage_coeff: float = 0.0):
        self.order_books: Dict[str, OrderBook] = {}  # symbol -> OrderBook
        # configure execution model and account fees
        self.execution = ExecutionModel(fee=execution_fee, slippage_coeff=slippage_coeff)
        self.strategies: List[Any] = []
        self.time = 0.0
        self.last_prices: Dict[str, float] = {}
        self.account = Account(fee=execution_fee)
        # runtime trade log and turnover
        self.trade_log: List[Dict[str, Any]] = []
        self.turnover = 0.0

    def register_strategy(self, strat: Any) -> None:
        """Register a trading strategy with the engine."""
        self.strategies.append(strat)
        strat.on_init(self)

    def run_demo(self, data_source=None):
        # multi-symbol demo for market-maker and pairs
        if data_source is None:
            # Use synthetic data (original behavior)
            import numpy as np
            np.random.seed(42)
            n = 200
            # build two cointegrated series
            x = np.cumsum(np.random.normal(scale=0.1, size=n)) + 100.0
            beta = 1.5
            y = beta * x + 0.5 + np.random.normal(scale=0.2, size=n)

            # initialize a simple top-of-book for demo symbols
            self.order_books['X'] = OrderBook()
            self.order_books['X'].update_from_snapshot([(99.0, 100)], [(101.0, 100)])
            self.order_books['Y'] = OrderBook()
            self.order_books['Y'].update_from_snapshot([(148.0, 100)], [(152.0, 100)])

            for i in range(n):
                evx = MarketEvent(timestamp=float(i), type="TRADE", symbol="X", price=float(x[i]), size=1.0, side=None)
                evy = MarketEvent(timestamp=float(i), type="TRADE", symbol="Y", price=float(y[i]), size=1.0, side=None)
                self._process_market_event(evx)
                self._process_market_event(evy)
        else:
            # Use real data from data_source
            from ..data import get_data_source
            ds = get_data_source(data_source) if isinstance(data_source, str) else data_source

            # Get data for symbols used by strategies
            symbols = set()
            for strat in self.strategies:
                if hasattr(strat, 'symbol'):
                    symbols.add(strat.symbol)
                elif hasattr(strat, 'symbol_x') and hasattr(strat, 'symbol_y'):
                    symbols.add(strat.symbol_x)
                    symbols.add(strat.symbol_y)

            # Default date range
            start_date = "2023-01-01"
            end_date = "2024-01-01"

            for symbol in symbols:
                df = ds.get_prices(symbol, start_date, end_date)
                if df is not None and not df.empty:
                    # Initialize order book
                    self.order_books[symbol] = OrderBook()
                    # Use last price for initial book
                    last_price = df['price'].iloc[-1]
                    spread = last_price * DEFAULT_SPREAD_PCT
                    bid = last_price - spread/2
                    ask = last_price + spread/2
                    self.order_books[symbol].update_from_snapshot([(bid, 100)], [(ask, 100)])

                    # Generate events - use itertuples for better performance
                    for row in df.itertuples():
                        ev = MarketEvent(
                            timestamp=float(row.timestamp),
                            type="TRADE",
                            symbol=symbol,
                            price=float(row.price),
                            size=1.0,
                            side=None
                        )
                        self._process_market_event(ev)

    def _process_market_event(self, ev: MarketEvent):
        # record last price per symbol
        self.last_prices[ev.symbol] = ev.price
        # apply trade to order book (so market trades can hit resting orders)
        if ev.type == "TRADE":
            self.order_books.setdefault(ev.symbol, OrderBook()).apply_trade(ev.price, ev.size)
            # process market trade against resting limit orders
            fills_from_book = self.order_books[ev.symbol].process_trade(ev.price, ev.size)
            for fdict in fills_from_book:
                # create a FillEvent applying slippage/fee using the ExecutionModel
                fill = self.execution.fill_from_book(
                    order_id=fdict.get('order_id'),
                    side=fdict.get('side'),
                    price=fdict.get('price'),
                    quantity=fdict.get('quantity'),
                    timestamp=ev.timestamp,
                    order_book=self.order_books[ev.symbol],
                )
                # set symbol from trade if available
                fill.symbol = ev.symbol
                # account and notify
                try:
                    self.account.on_fill(fill)
                except Exception as e:
                    logger.warning(f"Failed to process fill {fill.order_id} for account: {e}", exc_info=True)
                for s in self.strategies:
                    try:
                        s.on_order_filled(fill)
                    except Exception as e:
                        logger.warning(f"Strategy {type(s).__name__} failed to process fill {fill.order_id}: {e}", exc_info=True)
                # record trade log and turnover
                self.trade_log.append({'timestamp': fill.timestamp, 'order_id': fill.order_id, 'symbol': fill.symbol, 'side': fill.side, 'price': fill.price, 'quantity': fill.quantity, 'fee': fill.fee})
                self.turnover += abs(fill.price * fill.quantity)

        # give event to strategies
        orders = []
        for s in self.strategies:
            orders.extend(s.on_market_event(ev))

        # process orders (limit orders will be added to the book; market orders may fill immediately)
        for o in orders:
            # Ensure order book exists for the symbol
            if o.symbol not in self.order_books:
                self.order_books[o.symbol] = OrderBook()
            fill: Optional[FillEvent] = self.execution.simulate_fill(o, order_book=self.order_books.get(o.symbol))
            if fill:
                # update account and inform strategies
                try:
                    self.account.on_fill(fill)
                except Exception as e:
                    logger.warning(f"Failed to process fill {fill.order_id} for account: {e}", exc_info=True)
                for s in self.strategies:
                    try:
                        s.on_order_filled(fill)
                    except Exception as e:
                        logger.warning(f"Strategy {type(s).__name__} failed to process fill {fill.order_id}: {e}", exc_info=True)
                # record trade log and turnover
                self.trade_log.append({'timestamp': fill.timestamp, 'order_id': fill.order_id, 'symbol': fill.symbol, 'side': fill.side, 'price': fill.price, 'quantity': fill.quantity, 'fee': fill.fee})
                self.turnover += abs(fill.price * float(fill.quantity))

        # after processing orders and fills, record MTM equity using last_prices
        try:
            self.account.mark_to_market(ev.timestamp, self.last_prices)
        except Exception as e:
            # be tolerant in demo mode but log for debugging
            logger.debug(f"Mark-to-market failed at timestamp {ev.timestamp}: {e}", exc_info=True)
