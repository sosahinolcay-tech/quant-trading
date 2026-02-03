from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from data_platform.schemas import PriceBar


def _date_key(ts: float) -> str:
    return datetime.utcfromtimestamp(float(ts)).date().isoformat()


def save_price_bars(bars: Iterable[PriceBar], root_dir: str) -> List[str]:
    root = Path(root_dir)
    root.mkdir(parents=True, exist_ok=True)
    grouped = defaultdict(list)
    for bar in bars:
        grouped[_date_key(bar.timestamp)].append(bar.to_dict())

    written = []
    for date_key, rows in grouped.items():
        df = pd.DataFrame(rows)
        if df.empty:
            continue
        symbol = df["symbol"].iloc[0]
        target_dir = root / f"symbol={symbol}" / f"date={date_key}"
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / "prices.parquet"
        df.to_parquet(path, index=False)
        written.append(str(path))
    return written


def read_price_bars(
    root_dir: str, symbol: str, start: Optional[str] = None, end: Optional[str] = None
) -> pd.DataFrame:
    root = Path(root_dir) / f"symbol={symbol}"
    if not root.exists():
        return pd.DataFrame()

    frames = []
    for date_dir in root.glob("date=*"):
        if not date_dir.is_dir():
            continue
        date_key = date_dir.name.split("date=")[-1]
        if start and date_key < start:
            continue
        if end and date_key > end:
            continue
        path = date_dir / "prices.parquet"
        if path.exists():
            frames.append(pd.read_parquet(path))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
