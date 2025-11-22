import itertools
import csv
from pathlib import Path
from qt.engine.engine import SimulationEngine
from qt.strategies.market_maker import SimpleMarketMaker, AvellanedaMarketMaker
from qt.analytics.metrics import compute_returns, compute_sharpe, compute_drawdown


def run_demo_with_params(base_spread, inventory_coeff, execution_fee=0.0005, slippage_coeff=0.0001, strategy="simple"):
    # demo engine with configurable execution fee and slippage
    eng = SimulationEngine(execution_fee=execution_fee, slippage_coeff=slippage_coeff)
    if strategy == "avellaneda":
        mm = AvellanedaMarketMaker(symbol='TEST', size=1.0, base_spread=base_spread, risk_aversion=inventory_coeff)
    else:
        mm = SimpleMarketMaker(symbol='TEST', base_spread=base_spread, inventory_coeff=inventory_coeff)
    eng.register_strategy(mm)
    eng.run_demo()
    # return equity history (timestamp, equity) and engine for trade log access
    return eng.account.equity_history, eng


def sweep_and_save(spreads, inv_coeffs, out_csv="sweep_results.csv", strategy="simple"):
    rows = [("spread", "inv_coeff", "strategy", "execution_fee", "slippage_coeff", "final_equity", "sharpe", "max_drawdown", "turnover", "equity_path", "trades_path")]
    out_dir = Path("notebooks")
    out_dir.mkdir(parents=True, exist_ok=True)
    for s, ic, ef, sc in itertools.product(spreads, inv_coeffs, [0.0000, 0.0005, 0.001], [0.0, 0.0001, 0.0005]):
        history, eng = run_demo_with_params(s, ic, execution_fee=ef, slippage_coeff=sc, strategy=strategy)
        turnover = None
        trades_path = ""
        if not history:
            final_equity = None
            sharpe = None
            max_dd = None
            equity_path = ""
        else:
            # history is list of (timestamp, equity)
            fname = out_dir / f"equity_s{s}_i{ic}_ef{ef}_sc{sc}.csv"
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
            trades_fname = out_dir / f"trades_s{s}_i{ic}_ef{ef}_sc{sc}.csv"
            with open(trades_fname, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(("timestamp", "order_id", "symbol", "side", "price", "quantity", "fee"))
                turnover = 0.0
                for t in eng.trade_log:
                    w.writerow((t['timestamp'], t['order_id'], t.get('symbol'), t.get('side'), t.get('price'), t.get('quantity'), t.get('fee')))
                    turnover += abs(float(t.get('price')) * float(t.get('quantity')))
            trades_path = str(trades_fname)
    rows.append((s, ic, strategy, ef, sc, final_equity, sharpe, max_dd, turnover, equity_path, trades_path))
    with open(out_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


if __name__ == "__main__":
    sweep_and_save([0.5, 1.0, 1.5], [0.0, 0.1, 0.2])
