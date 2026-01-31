import itertools
import csv
from pathlib import Path
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker, AvellanedaMarketMaker
from qt.strategies.pairs import PairsStrategy
from qt.analytics.metrics import compute_returns, compute_sharpe, compute_drawdown


def run_demo_with_params(strategy="simple", **params):
    # demo engine with configurable execution fee and slippage
    execution_fee = params.get("execution_fee", 0.0005)
    slippage_coeff = params.get("slippage_coeff", 0.0001)
    eng = SimulationEngine(execution_fee=execution_fee, slippage_coeff=slippage_coeff)
    if strategy == "avellaneda":
        mm = AvellanedaMarketMaker(
            symbol="X", size=1.0, base_spread=params.get("base_spread", 0.01), risk_aversion=params.get("risk_aversion", 0.1)
        )
        eng.register_strategy(mm)
    elif strategy == "pairs":
        pairs = PairsStrategy(
            symbol_x="X",
            symbol_y="Y",
            window=params.get("window", 100),
            entry_z=params.get("entry_z", 2.0),
            exit_z=params.get("exit_z", 0.5),
            quantity=params.get("quantity", 100.0),
        )
        eng.register_strategy(pairs)
    else:
        mm = SimpleMarketMaker(
            symbol="X", base_spread=params.get("base_spread", 1.0), inventory_coeff=params.get("inventory_coeff", 0.1)
        )
        eng.register_strategy(mm)
    eng.run_demo()
    # return equity history (timestamp, equity) and engine for trade log access
    return eng.account.equity_history, eng


def sweep_and_save(strategy="simple", param_combos=None, out_csv="sweep_results.csv"):
    if param_combos is None:
        if strategy == "pairs":
            param_combos = itertools.product(
                [50, 100, 150], [1.0, 1.5, 2.0], [0.3, 0.5, 0.8], [50, 100, 200], [0.0000, 0.0005], [0.0, 0.0001]
            )
            param_names = ["window", "entry_z", "exit_z", "quantity", "execution_fee", "slippage_coeff"]
        else:
            param_combos = itertools.product([0.5, 1.0, 1.5], [0.0, 0.1, 0.2], [0.0000, 0.0005, 0.001], [0.0, 0.0001, 0.0005])
            param_names = ["base_spread", "inventory_coeff", "execution_fee", "slippage_coeff"]
    else:
        # If param_combos is provided, we need param_names too
        # Default to simple market maker param names if not provided
        if strategy == "pairs":
            param_names = ["window", "entry_z", "exit_z", "quantity", "execution_fee", "slippage_coeff"]
        else:
            param_names = ["base_spread", "inventory_coeff", "execution_fee", "slippage_coeff"]

    rows = [param_names + ["strategy", "final_equity", "sharpe", "max_drawdown", "turnover", "equity_path", "trades_path"]]
    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    for combo in param_combos:
        params = dict(zip(param_names, combo))
        history, eng = run_demo_with_params(strategy, **params)
        turnover = None
        trades_path = ""
        if not history:
            final_equity = None
            sharpe = None
            max_dd = None
            equity_path = ""
        else:
            # history is list of (timestamp, equity)
            fname_parts = [f"{k}{v}" for k, v in params.items() if k not in ["strategy", "execution_fee", "slippage_coeff"]]
            fname = out_dir / f"equity_{'_'.join(fname_parts)}.csv"
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
            # save trades and compute turnover
            trades_fname = out_dir / f"trades_{'_'.join(fname_parts)}.csv"
            with open(trades_fname, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(("timestamp", "order_id", "symbol", "side", "price", "quantity", "fee"))
                turnover = 0.0
                for t in eng.trade_log:
                    w.writerow(
                        (
                            t["timestamp"],
                            t["order_id"],
                            t.get("symbol"),
                            t.get("side"),
                            t.get("price"),
                            t.get("quantity"),
                            t.get("fee"),
                        )
                    )
                    turnover += abs(float(t.get("price", 0)) * float(t.get("quantity", 0)))
            trades_path = str(trades_fname)
        row = list(combo) + [strategy, final_equity, sharpe, max_dd, turnover, equity_path, trades_path]
        rows.append(row)
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


if __name__ == "__main__":
    # Example: sweep for simple market maker
    sweep_and_save("simple")
    # For pairs: sweep_and_save("pairs")
