from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List


def save_run_artifacts(
    run_name: str,
    config: Dict[str, Any],
    summary: Dict[str, Any],
    equity_history: List,
    trade_log: List,
    out_dir: str = "runs",
) -> str:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_name": run_name,
        "config": config,
        "summary": summary,
        "equity_history": [{"timestamp": float(ts), "equity": float(eq)} for ts, eq in equity_history],
        "trade_log": trade_log,
    }
    out_file = out_path / f"{run_name}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_file)
