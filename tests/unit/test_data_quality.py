import pandas as pd
from qt.data.prep import data_quality_report


def test_data_quality_report_basic():
    df = pd.DataFrame(
        {
            "timestamp": [1, 2, 3, 3, 4],
            "price": [100, 101, 102, 102, 103],
        }
    )
    report = data_quality_report(df, expected_freq_seconds=1)
    assert report["rows"] == 5
    assert report["duplicate_pct"] > 0
    assert report["coverage_pct"] > 0
