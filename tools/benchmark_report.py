"""Generate performance benchmark report."""
import sys
import time
from pathlib import Path
import json

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker, AvellanedaMarketMaker
from qt.strategies.pairs import PairsStrategy
from qt.analytics.metrics import compute_sharpe, compute_drawdown, compute_returns


def benchmark_engine_init(n=100):
    """Benchmark engine initialization."""
    start = time.time()
    for _ in range(n):
        eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    duration = time.time() - start
    return {
        "operation": "engine_initialization",
        "iterations": n,
        "total_time_sec": duration,
        "avg_time_ms": (duration / n) * 1000,
        "throughput_per_sec": n / duration
    }


def benchmark_market_maker_demo():
    """Benchmark market maker demo."""
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    mm = SimpleMarketMaker(symbol='X', base_spread=1.0)
    eng.register_strategy(mm)
    
    start = time.time()
    eng.run_demo()
    duration = time.time() - start
    
    return {
        "operation": "market_maker_demo",
        "duration_sec": duration,
        "events_processed": len(eng.account.equity_history),
        "trades": len(eng.trade_log),
        "throughput_events_per_sec": len(eng.account.equity_history) / duration if duration > 0 else 0
    }


def benchmark_pairs_demo():
    """Benchmark pairs trading demo."""
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    pairs = PairsStrategy(symbol_x='X', symbol_y='Y', window=50, entry_z=2.0, exit_z=0.5)
    eng.register_strategy(pairs)
    
    start = time.time()
    eng.run_demo()
    duration = time.time() - start
    
    return {
        "operation": "pairs_trading_demo",
        "duration_sec": duration,
        "events_processed": len(eng.account.equity_history),
        "trades": len(eng.trade_log),
        "throughput_events_per_sec": len(eng.account.equity_history) / duration if duration > 0 else 0
    }


def benchmark_metrics_computation(n=100):
    """Benchmark metrics computation."""
    import numpy as np
    np.random.seed(42)
    base = 100000.0
    returns = np.random.normal(0.001, 0.02, 1000)
    equity = [base]
    for r in returns:
        equity.append(equity[-1] * (1 + r))
    
    start = time.time()
    for _ in range(n):
        rets = compute_returns(equity)
        sharpe = compute_sharpe(rets)
        drawdown = compute_drawdown(equity)
    duration = time.time() - start
    
    return {
        "operation": "metrics_computation",
        "iterations": n,
        "total_time_sec": duration,
        "avg_time_ms": (duration / n) * 1000,
        "throughput_per_sec": n / duration
    }


def benchmark_order_book_operations(n=1000):
    """Benchmark order book operations."""
    from qt.engine.order_book import OrderBook
    from qt.engine.event import OrderEvent
    
    ob = OrderBook()
    ob.update_from_snapshot([(99.0, 100)], [(101.0, 100)])
    
    start = time.time()
    for i in range(n):
        order = OrderEvent(
            order_id=f"test-{i}",
            timestamp=float(i),
            symbol="X",
            side="BUY" if i % 2 == 0 else "SELL",
            price=100.0 + (i % 10) * 0.1,
            quantity=1.0,
            order_type="LIMIT"
        )
        ob.add_limit_order(order)
    duration = time.time() - start
    
    return {
        "operation": "order_book_operations",
        "iterations": n,
        "total_time_sec": duration,
        "avg_time_us": (duration / n) * 1_000_000,
        "throughput_per_sec": n / duration
    }


def generate_report():
    """Generate comprehensive benchmark report."""
    print("Running performance benchmarks...")
    print("=" * 60)
    
    results = []
    
    # Run benchmarks
    print("\n1. Engine Initialization...")
    results.append(benchmark_engine_init(100))
    
    print("2. Market Maker Demo...")
    results.append(benchmark_market_maker_demo())
    
    print("3. Pairs Trading Demo...")
    results.append(benchmark_pairs_demo())
    
    print("4. Metrics Computation...")
    results.append(benchmark_metrics_computation(100))
    
    print("5. Order Book Operations...")
    results.append(benchmark_order_book_operations(1000))
    
    # Generate report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "benchmarks": results
    }
    
    # Save JSON report
    out_dir = Path("notebooks")
    out_dir.mkdir(exist_ok=True)
    report_path = out_dir / "benchmark_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK REPORT SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"\n{r['operation']}:")
        if 'avg_time_ms' in r:
            print(f"  Average time: {r['avg_time_ms']:.2f} ms")
        if 'duration_sec' in r:
            print(f"  Duration: {r['duration_sec']:.3f} s")
        if 'throughput_per_sec' in r:
            print(f"  Throughput: {r['throughput_per_sec']:.0f} ops/s")
        if 'trades' in r:
            print(f"  Trades: {r['trades']}")
    
    print(f"\n✓ Full report saved to: {report_path}")
    return report


if __name__ == "__main__":
    generate_report()

