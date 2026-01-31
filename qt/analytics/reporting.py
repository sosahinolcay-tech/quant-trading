from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List


def _render_html(summary: Dict[str, Any], equity_history: List, trade_log: List) -> str:
    rows = "\n".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in summary.items()
    )
    equity_rows = "\n".join(
        f"<tr><td>{float(ts):.2f}</td><td>{float(eq):.2f}</td></tr>" for ts, eq in equity_history[-50:]
    )
    trade_rows = "\n".join(
        f"<tr><td>{t.get('timestamp')}</td><td>{t.get('symbol')}</td><td>{t.get('side')}</td><td>{t.get('price')}</td><td>{t.get('quantity')}</td></tr>"
        for t in trade_log[-50:]
    )
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Quant Trading Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #0f172a; }}
    h1 {{ margin-bottom: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 8px; font-size: 12px; }}
    th {{ background: #f1f5f9; text-align: left; }}
    .muted {{ color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
  <h1>Quant Trading Report</h1>
  <div class="muted">Summary metrics and recent activity snapshot.</div>
  <h2>Summary</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    {rows}
  </table>
  <h2>Recent Equity Points</h2>
  <table>
    <tr><th>Timestamp</th><th>Equity</th></tr>
    {equity_rows}
  </table>
  <h2>Recent Trades</h2>
  <table>
    <tr><th>Timestamp</th><th>Symbol</th><th>Side</th><th>Price</th><th>Quantity</th></tr>
    {trade_rows}
  </table>
</body>
</html>
"""


def generate_run_report(
    run_name: str,
    summary: Dict[str, Any],
    equity_history: List,
    trade_log: List,
    out_dir: str = "reports",
) -> Dict[str, str]:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    html_path = out_path / f"{run_name}.html"
    html_path.write_text(_render_html(summary, equity_history, trade_log), encoding="utf-8")

    pdf_path = out_path / f"{run_name}.pdf"
    pdf_written = False
    try:
        from weasyprint import HTML

        HTML(string=html_path.read_text(encoding="utf-8")).write_pdf(str(pdf_path))
        pdf_written = True
    except Exception:
        pdf_path = None

    return {"html": str(html_path), "pdf": str(pdf_path) if pdf_written and pdf_path else ""}
