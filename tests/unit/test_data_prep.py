import pandas as pd
import numpy as np

from qt.data.prep import prepare_price_frame


def test_prepare_price_frame_normalizes_and_validates():
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "Close": [100.0, 101.0, 0.0, 102.0, np.nan],
        }
    )
    prepared, issues = prepare_price_frame(df, min_rows=2)
    assert "timestamp" in prepared.columns
    assert "price" in prepared.columns
    assert "returns" in prepared.columns
    assert prepared["price"].min() > 0
    assert issues == {}
