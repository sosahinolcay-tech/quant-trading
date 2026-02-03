import pandas as pd

from data_platform.quality import price_quality_report


def test_price_quality_report_basic():
    df = pd.DataFrame(
        {
            "timestamp": [1, 2, 2],
            "price_open": [100, 101, 101],
            "price_high": [102, 103, 103],
            "price_low": [99, 100, 100],
            "price_close": [101, 102, 102],
            "volume": [1000, 1200, 1200],
        }
    )
    report = price_quality_report(df)
    assert report["rows"] == 3.0
    assert report["duplicate_pct"] > 0.0
    assert report["missing_pct"] == 0.0
