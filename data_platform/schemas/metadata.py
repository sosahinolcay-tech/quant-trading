from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    status: str
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    last_latency_ms: Optional[float] = None
    supported_domains: Optional[List[str]] = None
    rate_limit: Optional[str] = None
