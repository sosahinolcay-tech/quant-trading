import csv
from collections import defaultdict
from datetime import datetime
from .metrics import compute_returns, compute_sharpe, compute_drawdown


def _to_daily_buckets(equity_history):
    """Group equity_history (list of (timestamp, equity)) by date (YYYY-MM-DD).

    Returns dict date_str -> list of (timestamp, equity)
    """
    days = defaultdict(list)
    for ts, eq in equity_history:
        # assume ts is numeric epoch or convertible
        try:
            dt = datetime.fromtimestamp(float(ts))
            key = dt.date().isoformat()
        except Exception:
            key = str(ts)
        days[key].append((ts, eq))
    return days


def _period_metrics(equity_pairs):
    """Compute simple metrics for a period given list of (ts, equity)."""
    equities = [eq for (_ts, eq) in equity_pairs]
    if len(equities) < 2:
        return {"final_equity": equities[-1] if equities else None, "returns": [], "sharpe": None, "max_drawdown": None}
    rets = compute_returns(equities)
    sharpe = compute_sharpe(rets)
    dd = compute_drawdown(equities)
    return {"final_equity": equities[-1], "returns": rets.tolist(), "sharpe": sharpe, "max_drawdown": dd.get("max_drawdown")}


def daily_summary(equity_history, out_csv_path=None):
    """Produce daily summaries for the provided equity_history.

    equity_history: list of (timestamp, equity)
    Returns dict date -> metrics
    If out_csv_path provided, writes CSV with daily stats.
    """
    days = _to_daily_buckets(equity_history)
    result = {}
    rows = [("date", "final_equity", "sharpe", "max_drawdown", "n_points")]
    for d in sorted(days.keys()):
        metrics = _period_metrics(days[d])
        result[d] = metrics
        rows.append((d, metrics.get("final_equity"), metrics.get("sharpe"), metrics.get("max_drawdown"), len(days[d])))
    if out_csv_path:
        with open(out_csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerows(rows)
    return result


def weekly_summary(equity_history, out_csv_path=None):
    """Produce simple weekly summaries by ISO week number.

    Returns dict week_key -> metrics where week_key is 'YYYY-WW'.
    """
    weeks = defaultdict(list)
    for ts, eq in equity_history:
        try:
            dt = datetime.fromtimestamp(float(ts))
            key = f"{dt.isocalendar()[0]}-{dt.isocalendar()[1]:02d}"
        except Exception:
            key = str(ts)
        weeks[key].append((ts, eq))
    result = {}
    rows = [("week", "final_equity", "sharpe", "max_drawdown", "n_points")]
    for wk in sorted(weeks.keys()):
        metrics = _period_metrics(weeks[wk])
        result[wk] = metrics
        rows.append((wk, metrics.get("final_equity"), metrics.get("sharpe"), metrics.get("max_drawdown"), len(weeks[wk])))
    if out_csv_path:
        with open(out_csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerows(rows)
    return result


def full_report(equity_history, trade_log=None, out_csv_path="summary_metrics.csv"):
    """Generate a full report: overall metrics plus optional daily/weekly CSVs.

    equity_history: list of (timestamp, equity) or a plain list of equity values.
    trade_log: optional list of trade dicts (timestamp, order_id, symbol, side, price, quantity, fee)
    Returns summary dict.
    """
    # support legacy input: plain equity list
    if equity_history and not isinstance(equity_history[0], (list, tuple)):
        equities = equity_history
        rets = compute_returns(equities)
        sharpe = compute_sharpe(rets)
        dd = compute_drawdown(equities)
        rows = [
            ("metric", "value"),
            ("sharpe", sharpe),
            ("max_drawdown", dd["max_drawdown"]),
            ("final_equity", equities[-1] if equities else None),
        ]
        with open(out_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return {"sharpe": sharpe, "max_drawdown": dd["max_drawdown"]}

    # otherwise assume list of (ts, equity)
    # overall
    equities = [eq for (_ts, eq) in equity_history]
    rets = compute_returns(equities)
    sharpe = compute_sharpe(rets)
    dd = compute_drawdown(equities)
    summary = {
        "sharpe": sharpe,
        "max_drawdown": dd.get("max_drawdown"),
        "final_equity": equities[-1] if equities else None,
        "n_points": len(equities),
    }

    # write top-level CSV
    rows = [("metric", "value")]
    for k, v in summary.items():
        rows.append((k, v))
    with open(out_csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    # optionally write daily and weekly CSVs beside the main file
    base = out_csv_path.rsplit(".", 1)[0]
    daily_csv = f"{base}_daily.csv"
    weekly_csv = f"{base}_weekly.csv"
    daily_summary(equity_history, out_csv_path=daily_csv)
    weekly_summary(equity_history, out_csv_path=weekly_csv)

    # optionally include trade-level aggregates if trade_log provided
    if trade_log:
        total_trades = len(trade_log)
        turnover = sum(abs(float(t.get("price", 0)) * float(t.get("quantity", 0))) for t in trade_log)
        summary.update({"total_trades": total_trades, "turnover": turnover})
        # augment main CSV
        with open(out_csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("total_trades", total_trades))
            writer.writerow(("turnover", turnover))

    return summary


def summary_report(equity_curve, out_csv_path="summary_metrics.csv"):
    """Backward-compatible wrapper kept for callers that pass a plain equity list."""
    return full_report(equity_curve, trade_log=None, out_csv_path=out_csv_path)
