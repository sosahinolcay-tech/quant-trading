from __future__ import annotations

from typing import Optional

import pandas as pd
def fetch_yahoo_chart(symbol: str, interval: str = "1d", range_str: str = "2y") -> Optional[pd.DataFrame]:
    """Fetch data from Yahoo chart endpoint as a fallback."""
    try:
        import requests
    except Exception:
        return None
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": interval, "range": range_str}
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code != 200:
        return None
    payload = resp.json()
    chart = payload.get("chart", {})
    result = chart.get("result", [])
    if not result:
        return None
    data = result[0]
    timestamps = data.get("timestamp", [])
    indicators = data.get("indicators", {})
    quote = indicators.get("quote", [{}])[0]
    closes = quote.get("close", [])
    if not timestamps or not closes:
        return None
    df = pd.DataFrame({"timestamp": timestamps, "price": closes})
    return df
