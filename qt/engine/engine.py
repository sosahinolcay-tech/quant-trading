from typing import List
from ..engine.event import MarketEvent, OrderEvent, FillEvent
from .order_book import OrderBook
from .execution import ExecutionModel
from ..risk.accounting import Account


class SimulationEngine:
    def __init__(self, execution_fee: float = 0.0, slippage_coeff: float = 0.0):
        self.order_book = OrderBook()
        # configure execution model and account fees
        self.execution = ExecutionModel(fee=execution_fee, slippage_coeff=slippage_coeff)
        self.strategies = []
        self.time = 0.0
        self.last_prices = {}
        self.account = Account(fee=execution_fee)

    def register_strategy(self, strat):
        self.strategies.append(strat)
        strat.on_init(self)

    def run_demo(self):
        # multi-symbol synthetic demo for market-maker and pairs
        import numpy as np
        np.random.seed(42)
        n = 200
        t = np.arange(n)
        # build two cointegrated series
        x = np.cumsum(np.random.normal(scale=0.1, size=n)) + 100.0
        beta = 1.5
        y = beta * x + 0.5 + np.random.normal(scale=0.2, size=n)

        # initialize a simple top-of-book for a demo symbol
        self.order_book.update_from_snapshot([(99.0, 100)], [(101.0, 100)])

        for i in range(n):
            evx = MarketEvent(timestamp=float(i), type="TRADE", symbol="X", price=float(x[i]), size=1.0, side=None)
            evy = MarketEvent(timestamp=float(i), type="TRADE", symbol="Y", price=float(y[i]), size=1.0, side=None)
            self._process_market_event(evx)
            self._process_market_event(evy)

    def _process_market_event(self, ev: MarketEvent):
        # record last price per symbol
        self.last_prices[ev.symbol] = ev.price
        # update order book for the demo "TEST" symbol if present
        if ev.symbol == "TEST" and ev.type == "TRADE":
            self.order_book.apply_trade(ev.price, ev.size)

        # give event to strategies
        orders = []
        for s in self.strategies:
            orders.extend(s.on_market_event(ev))

        # process orders
        for o in orders:
            fill = self.execution.simulate_fill(o)
            # update account and inform strategies
            try:
                self.account.on_fill(fill)
            except Exception:
                pass
            for s in self.strategies:
                s.on_order_filled(fill)

        # after processing orders and fills, record MTM equity using last_prices
        try:
            self.account.mark_to_market(ev.timestamp, self.last_prices)
        except Exception:
            # be tolerant in demo mode
            pass
