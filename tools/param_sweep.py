import itertools
import csv
from pathlib import Path
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker
from qt.analytics.metrics import compute_returns, compute_sharpe, compute_drawdown


def run_demo_with_params(base_spread, inventory_coeff):
    # demo engine with small execution fee and slippage
    eng = SimulationEngine(execution_fee=0.0005, slippage_coeff=0.0001)
    mm = SimpleMarketMaker(symbol='TEST', base_spread=base_spread, inventory_coeff=inventory_coeff)
    eng.register_strategy(mm)
    eng.run_demo()
    # return equity history (timestamp, equity)
    return eng.account.equity_history


def sweep_and_save(spreads, inv_coeffs, out_csv="sweep_results.csv"):
    rows = [("spread", "inv_coeff", "final_equity", "sharpe", "max_drawdown", "equity_path")]
    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    for s, ic in itertools.product(spreads, inv_coeffs):
        history = run_demo_with_params(s, ic)
        if not history:
            final_equity = None
            sharpe = None
            max_dd = None
            equity_path = ""
        else:
            # history is list of (timestamp, equity)
            fname = out_dir / f"equity_s{s}_i{ic}.csv"
            with open(fname, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(("timestamp", "equity"))
                for ts, eq in history:
                    writer.writerow((ts, eq))
            equity_vals = [eq for (_, eq) in history]
            final_equity = equity_vals[-1]
            rets = compute_returns(equity_vals)
            sharpe = compute_sharpe(rets)
            max_dd = compute_drawdown(equity_vals)["max_drawdown"]
            equity_path = str(fname)
        rows.append((s, ic, final_equity, sharpe, max_dd, equity_path))
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


if __name__ == "__main__":
    sweep_and_save([0.5, 1.0, 1.5], [0.0, 0.1, 0.2])
