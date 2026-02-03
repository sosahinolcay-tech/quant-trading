from __future__ import annotations

from typing import Dict

import pandas as pd


def price_quality_report(df: pd.DataFrame) -> Dict[str, float]:
    if df is None or df.empty:
        return {"rows": 0.0, "missing_pct": 1.0, "duplicate_pct": 0.0, "out_of_range_pct": 0.0}

    required = ["timestamp", "price_open", "price_high", "price_low", "price_close", "volume"]
    missing = sum(1 for c in required if c not in df.columns)
    missing_pct = missing / max(len(required), 1)

    duplicate_pct = float(df.duplicated(subset=["timestamp"]).mean()) if "timestamp" in df.columns else 0.0

    out_of_range_pct = 0.0
    if all(c in df.columns for c in ["price_open", "price_high", "price_low", "price_close"]):
        invalid = (df["price_low"] > df["price_high"]) | (df["price_open"] < 0) | (df["price_close"] < 0)
        out_of_range_pct = float(invalid.mean()) if len(df) else 0.0

    return {
        "rows": float(len(df)),
        "missing_pct": float(missing_pct),
        "duplicate_pct": float(duplicate_pct),
        "out_of_range_pct": float(out_of_range_pct),
    }
