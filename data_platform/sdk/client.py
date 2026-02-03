from __future__ import annotations

from typing import Any, Dict, List

import requests


class DataPlatformClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8010"):
        self.base_url = base_url.rstrip("/")

    def prices(self, symbol: str, start: str, end: str, interval: str = "1d", source: str = "yahoo") -> List[Dict]:
        payload = {"symbol": symbol, "start": start, "end": end, "interval": interval, "source": source}
        return self._post("/data/prices", payload)

    def fundamentals(self, symbol: str, period: str = "annual", source: str = "yahoo") -> List[Dict]:
        payload = {"symbol": symbol, "period": period, "source": source}
        return self._post("/data/fundamentals", payload)

    def provider_status(self) -> List[Dict]:
        return self._get("/providers/status")

    def _post(self, path: str, payload: Dict[str, Any]) -> List[Dict]:
        resp = requests.post(f"{self.base_url}{path}", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str) -> List[Dict]:
        resp = requests.get(f"{self.base_url}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json()
