from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("timestamp", "price")


def _to_timestamp_series(df: pd.DataFrame) -> pd.Series:
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
    elif df.index.name or isinstance(df.index, pd.DatetimeIndex):
        ts = pd.to_datetime(df.index, errors="coerce")
    elif "Date" in df.columns:
        ts = pd.to_datetime(df["Date"], errors="coerce")
    else:
        ts = pd.Series([pd.NaT] * len(df))
    return ts


def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    out = df.copy()
    if "Close" in out.columns and "price" not in out.columns:
        out = out.rename(columns={"Close": "price"})

    if "price" not in out.columns:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    ts = _to_timestamp_series(out)
    out["timestamp"] = ts
    out = out.dropna(subset=["timestamp", "price"])
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out = out.dropna(subset=["price"])
    out = out[out["price"] > 0]
    out = out.sort_values("timestamp")
    out = out.drop_duplicates(subset=["timestamp"], keep="last")
    out["timestamp"] = out["timestamp"].astype("int64") // 10**9
    return out[["timestamp", "price"]]


def add_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        out["returns"] = []
        return out
    prices = out["price"].astype(float).values
    rets = np.zeros_like(prices, dtype=float)
    if len(prices) > 1:
        rets[1:] = prices[1:] / np.maximum(prices[:-1], 1e-12) - 1.0
    out["returns"] = rets
    return out


def validate_prices(df: pd.DataFrame, min_rows: int = 10) -> Tuple[bool, Dict[str, str]]:
    issues: Dict[str, str] = {}
    if df is None or df.empty:
        issues["empty"] = "No data returned from source."
        return False, issues
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        issues["missing_columns"] = f"Missing columns: {missing}"
    if df["price"].le(0).any():
        issues["non_positive"] = "Prices contain non-positive values."
    if df["timestamp"].isna().any():
        issues["missing_timestamp"] = "Timestamps contain missing values."
    if len(df) < min_rows:
        issues["too_short"] = f"Expected at least {min_rows} rows, got {len(df)}."
    is_valid = len(issues) == 0
    return is_valid, issues


def prepare_price_frame(df: pd.DataFrame, min_rows: int = 10) -> Tuple[pd.DataFrame, Dict[str, str]]:
    normalized = normalize_prices(df)
    normalized = add_returns(normalized)
    is_valid, issues = validate_prices(normalized, min_rows=min_rows)
    return normalized, issues
