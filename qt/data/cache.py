from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd


def _default_cache_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / ".cache" / "qt_data"


def cache_key(source: str, symbol: str, start_date: str, end_date: str, interval: str) -> str:
    key = f"{source}:{symbol}:{start_date}:{end_date}:{interval}".lower()
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def read_cache(key: str, cache_dir: Optional[Path] = None) -> Optional[pd.DataFrame]:
    cache_dir = cache_dir or _default_cache_dir()
    path = cache_dir / f"{key}.csv"
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def write_cache(key: str, df: pd.DataFrame, cache_dir: Optional[Path] = None) -> None:
    cache_dir = cache_dir or _default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{key}.csv"
    df.to_csv(path, index=False)
