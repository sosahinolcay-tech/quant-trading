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

    def run_demo(
        self,
        data_source: Optional[Any] = "yahoo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "1d",
        fallback_to_synthetic: bool = True,
    ):
        """Run a demo simulation using a data source or synthetic fallback."""
        from ..data import get_data_source, SyntheticDataSource

        # Determine symbols used by strategies
        symbols = set()
        for strat in self.strategies:
            if hasattr(strat, "symbol"):
                symbols.add(strat.symbol)
            if hasattr(strat, "symbol_x") and hasattr(strat, "symbol_y"):
                symbols.add(strat.symbol_x)
                symbols.add(strat.symbol_y)

        start_date = start_date or "2022-01-01"
        end_date = end_date or "2024-01-01"

        ds = get_data_source(data_source) if isinstance(data_source, str) else data_source
        if ds is None:
            ds = get_data_source("yahoo")

        for symbol in symbols:
            df = ds.get_prices(symbol, start_date, end_date, interval=interval)
            if (df is None or df.empty) and fallback_to_synthetic:
                logger.warning(f"Falling back to synthetic data for {symbol}")
                df = SyntheticDataSource().get_prices(symbol, start_date, end_date, interval=interval)
            if df is None or df.empty:
                logger.warning(f"No data available for {symbol}, skipping.")
                continue

            self.order_books[symbol] = OrderBook()
            last_price = df["price"].iloc[-1]
            spread = last_price * DEFAULT_SPREAD_PCT
            bid = last_price - spread / 2
            ask = last_price + spread / 2
            self.order_books[symbol].update_from_snapshot([(bid, 100)], [(ask, 100)])

            for row in df.itertuples():
                ev = MarketEvent(
                    timestamp=float(row.timestamp),
                    type="TRADE",
                    symbol=symbol,
                    price=float(row.price),
                    size=1.0,
                    side=None,
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
                fill_from_book: FillEvent = self.execution.fill_from_book(
                    order_id=fdict.get('order_id'),
                    side=fdict.get('side'),
                    price=fdict.get('price'),
                    quantity=fdict.get('quantity'),
                    timestamp=ev.timestamp,
                    order_book=self.order_books[ev.symbol],
                )
                # set symbol from trade if available
                fill_from_book.symbol = ev.symbol
                # account and notify
                try:
                    self.account.on_fill(fill_from_book)
                except Exception as e:
                    logger.warning(f"Failed to process fill {fill_from_book.order_id} for account: {e}", exc_info=True)
                for s in self.strategies:
                    try:
                        s.on_order_filled(fill_from_book)
                    except Exception as e:
                        logger.warning(f"Strategy {type(s).__name__} failed to process fill {fill_from_book.order_id}: {e}", exc_info=True)
                # record trade log and turnover
                self.trade_log.append({'timestamp': fill_from_book.timestamp, 'order_id': fill_from_book.order_id, 'symbol': fill_from_book.symbol, 'side': fill_from_book.side, 'price': fill_from_book.price, 'quantity': fill_from_book.quantity, 'fee': fill_from_book.fee})
                self.turnover += abs(fill_from_book.price * fill_from_book.quantity)

        # give event to strategies
        orders = []
        for s in self.strategies:
            orders.extend(s.on_market_event(ev))

        # process orders (limit orders will be added to the book; market orders may fill immediately)
        for o in orders:
            # Ensure order book exists for the symbol
            if o.symbol not in self.order_books:
                self.order_books[o.symbol] = OrderBook()
            fill_order: Optional[FillEvent] = self.execution.simulate_fill(o, order_book=self.order_books.get(o.symbol))
            if fill_order:
                # update account and inform strategies
                try:
                    self.account.on_fill(fill_order)
                except Exception as e:
                    logger.warning(f"Failed to process fill {fill_order.order_id} for account: {e}", exc_info=True)
                for s in self.strategies:
                    try:
                        s.on_order_filled(fill_order)
                    except Exception as e:
                        logger.warning(f"Strategy {type(s).__name__} failed to process fill {fill_order.order_id}: {e}", exc_info=True)
                # record trade log and turnover
                self.trade_log.append({'timestamp': fill_order.timestamp, 'order_id': fill_order.order_id, 'symbol': fill_order.symbol, 'side': fill_order.side, 'price': fill_order.price, 'quantity': fill_order.quantity, 'fee': fill_order.fee})
                self.turnover += abs(fill_order.price * float(fill_order.quantity))

        # after processing orders and fills, record MTM equity using last_prices
        try:
            self.account.mark_to_market(ev.timestamp, self.last_prices)
        except Exception as e:
            # be tolerant in demo mode but log for debugging
            logger.debug(f"Mark-to-market failed at timestamp {ev.timestamp}: {e}", exc_info=True)
