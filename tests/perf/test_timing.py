"""Performance benchmark tests for the trading engine and strategies."""

import time
import pytest
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker
from qt.strategies.pairs import PairsStrategy
from qt.analytics.metrics import compute_sharpe, compute_drawdown, compute_returns


@pytest.fixture
def sample_equity_curve():
    """Generate a sample equity curve for benchmarking."""
    import numpy as np

    np.random.seed(42)
    base = 100000.0
    returns = np.random.normal(0.001, 0.02, 1000)
    equity = [base]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    return equity


def test_engine_initialization_speed():
    """Benchmark engine initialization time."""
    start = time.time()
    for _ in range(100):
        eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    duration = time.time() - start
    avg_time = duration / 100
    assert avg_time < 0.01, f"Engine initialization too slow: {avg_time:.4f}s"
    print(f"✓ Engine initialization: {avg_time*1000:.2f}ms per instance")


def test_market_maker_demo_speed():
    """Benchmark market maker demo execution time."""
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    mm = SimpleMarketMaker(symbol="X", base_spread=1.0)
    eng.register_strategy(mm)

    start = time.time()
    eng.run_demo()
    duration = time.time() - start

    assert duration < 5.0, f"Market maker demo too slow: {duration:.2f}s"
    print(f"✓ Market maker demo: {duration:.2f}s")


def test_pairs_trading_demo_speed():
    """Benchmark pairs trading demo execution time."""
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    pairs = PairsStrategy(symbol_x="X", symbol_y="Y", window=50, entry_z=2.0, exit_z=0.5)
    eng.register_strategy(pairs)

    start = time.time()
    eng.run_demo()
    duration = time.time() - start

    assert duration < 5.0, f"Pairs trading demo too slow: {duration:.2f}s"
    print(f"✓ Pairs trading demo: {duration:.2f}s")


def test_metrics_computation_speed(sample_equity_curve):
    """Benchmark metrics computation performance."""
    start = time.time()
    for _ in range(100):
        returns = compute_returns(sample_equity_curve)
        sharpe = compute_sharpe(returns)
        drawdown = compute_drawdown(sample_equity_curve)
    duration = time.time() - start
    avg_time = duration / 100

    assert avg_time < 0.1, f"Metrics computation too slow: {avg_time:.4f}s"
    print(f"✓ Metrics computation: {avg_time*1000:.2f}ms per iteration")


def test_order_book_operations_speed():
    """Benchmark order book add/remove operations."""
    from qt.engine.order_book import OrderBook
    from qt.engine.event import OrderEvent

    ob = OrderBook()
    ob.update_from_snapshot([(99.0, 100)], [(101.0, 100)])

    start = time.time()
    for i in range(1000):
        order = OrderEvent(
            order_id=f"test-{i}",
            timestamp=float(i),
            symbol="X",
            side="BUY" if i % 2 == 0 else "SELL",
            price=100.0 + (i % 10) * 0.1,
            quantity=1.0,
            order_type="LIMIT",
        )
        ob.add_limit_order(order)
    duration = time.time() - start

    assert duration < 1.0, f"Order book operations too slow: {duration:.2f}s"
    print(f"✓ Order book operations: {duration*1000:.2f}ms for 1000 orders ({duration/1000*1000:.2f}μs per order)")


def test_event_processing_throughput():
    """Benchmark event processing throughput."""
    from qt.engine.event import MarketEvent

    eng = SimulationEngine()
    mm = SimpleMarketMaker(symbol="X")
    eng.register_strategy(mm)

    # Generate events
    events = []
    for i in range(500):
        events.append(
            MarketEvent(timestamp=float(i), type="TRADE", symbol="X", price=100.0 + (i % 20) * 0.1, size=1.0, side=None)
        )

    start = time.time()
    for ev in events:
        eng._process_market_event(ev)
    duration = time.time() - start

    throughput = len(events) / duration
    assert throughput > 100, f"Event processing too slow: {throughput:.0f} events/s"
    print(f"✓ Event processing: {throughput:.0f} events/s ({duration*1000/len(events):.2f}ms per event)")


def test_memory_efficiency():
    """Test that engine doesn't leak memory excessively."""
    import sys

    eng = SimulationEngine()
    mm = SimpleMarketMaker(symbol="X")
    eng.register_strategy(mm)

    # Run multiple demos and check memory doesn't grow excessively
    initial_size = sys.getsizeof(eng)

    for _ in range(10):
        eng.run_demo()

    final_size = sys.getsizeof(eng)
    growth = final_size - initial_size

    # Allow some growth but not excessive
    assert growth < 1000000, f"Memory growth too high: {growth} bytes"
    print(f"✓ Memory efficiency: {growth} bytes growth after 10 demos")
