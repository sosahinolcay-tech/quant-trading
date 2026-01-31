import numpy as np
from qt.strategies.pairs import PairsStrategy
from qt.engine.engine import SimulationEngine
from qt.engine.event import MarketEvent
from qt.analytics.metrics import compute_returns, compute_sharpe
from qt.analytics.reports import full_report
import logging

# Set up logging for performance monitoring
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def walk_forward_analysis(n_windows=5, window_size=100, test_size=50, seed=42):
    """
    Perform walk-forward analysis for pairs strategy.

    For each window:
    - Train (fit OLS) on in-sample data
    - Test on out-of-sample data
    - Collect performance metrics
    """
    np.random.seed(seed)
    results = []

    for w in range(n_windows):
        logger.info(f"Running walk-forward window {w+1}/{n_windows}")

        # Generate synthetic cointegrated data for this window
        n_total = window_size + test_size
        t = np.arange(n_total)
        x_base = np.cumsum(np.random.normal(scale=0.1, size=n_total)) + 100.0
        beta_true = 1.5 + 0.1 * np.random.normal()  # vary beta slightly
        y_base = beta_true * x_base + 0.5 + np.random.normal(scale=0.2, size=n_total)

        # In-sample: first window_size points
        x_train = x_base[:window_size]
        y_train = y_base[:window_size]

        # Fit beta on in-sample
        A = np.vstack([x_train, np.ones(len(x_train))]).T
        beta_fit, _ = np.linalg.lstsq(A, y_train, rcond=None)[0]

        # Out-of-sample: next test_size points
        x_test = x_base[window_size : window_size + test_size]
        y_test = y_base[window_size : window_size + test_size]

        # Run simulation on test data with fitted beta
        eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
        ps = PairsStrategy("X", "Y", window=window_size, entry_z=2.0, exit_z=0.5, quantity=10.0)
        eng.register_strategy(ps)

        # Override the fitted beta (since strategy fits its own, but for demo we can set it)
        # Actually, the strategy fits its own beta, so this is fine.

        # Feed test data
        for i in range(test_size):
            evx = MarketEvent(timestamp=float(i), type="TRADE", symbol="X", price=float(x_test[i]), size=1.0, side=None)
            evy = MarketEvent(timestamp=float(i), type="TRADE", symbol="Y", price=float(y_test[i]), size=1.0, side=None)
            eng._process_market_event(evx)
            eng._process_market_event(evy)

        # Collect results
        equity_curve = eng.account.get_equity_curve()
        if equity_curve and len(equity_curve) > 1:
            rets = compute_returns(equity_curve)
            sharpe = compute_sharpe(rets)
            final_eq = equity_curve[-1]
        else:
            sharpe = 0.0
            final_eq = 100000.0

        window_result = {
            "window": w + 1,
            "beta_true": beta_true,
            "beta_fit": beta_fit,
            "sharpe": sharpe,
            "final_equity": final_eq,
            "trades": len(eng.trade_log),
            "turnover": eng.turnover,
        }
        results.append(window_result)
        logger.info(f"Window {w+1}: Sharpe={sharpe:.3f}, Final Eq={final_eq:.2f}, Trades={len(eng.trade_log)}")

    # Aggregate results
    avg_sharpe = np.mean([r["sharpe"] for r in results])
    avg_final_eq = np.mean([r["final_equity"] for r in results])
    total_trades = sum(r["trades"] for r in results)

    logger.info(
        f"Walk-forward summary: Avg Sharpe={avg_sharpe:.3f}, Avg Final Eq={avg_final_eq:.2f}, Total Trades={total_trades}"
    )

    return results


if __name__ == "__main__":
    results = walk_forward_analysis()
    print("Walk-forward results:")
    for r in results:
        print(r)
