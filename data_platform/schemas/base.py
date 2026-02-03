from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BaseRecord:
    symbol: str
    timestamp: float
    source: str
    timezone: str = "UTC"
    currency: Optional[str] = None
    ingested_at: Optional[datetime] = None
    data_quality_score: Optional[float] = None
    provider_latency_ms: Optional[float] = None

    def to_dict(self) -> dict:
        out = asdict(self)
        if self.ingested_at is not None:
            out["ingested_at"] = self.ingested_at.isoformat()
        return out
