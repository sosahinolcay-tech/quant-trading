import csv
from .metrics import compute_returns, compute_sharpe, compute_drawdown


def summary_report(equity_curve, out_csv_path="summary_metrics.csv"):
    rets = compute_returns(equity_curve)
    sharpe = compute_sharpe(rets)
    dd = compute_drawdown(equity_curve)
    rows = [
        ("metric", "value"),
        ("sharpe", sharpe),
        ("max_drawdown", dd["max_drawdown"]),
        ("final_equity", equity_curve[-1] if len(equity_curve) else None),
    ]
    with open(out_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(r)
    return {"sharpe": sharpe, "max_drawdown": dd["max_drawdown"]}
