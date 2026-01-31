import numpy as np
from qt.ml.pipeline import FeatureBuilder, SimpleModelWrapper


def test_feature_builder_small():
    prices = np.array([100.0, 101.0, 100.5, 101.5, 102.0, 101.0, 100.0, 99.5, 100.5, 101.0, 101.5])
    fb = FeatureBuilder(
        window=3,
        ma_window=3,
        vol_window=3,
        rsi_window=3,
        boll_window=3,
        macd_fast=3,
        macd_slow=5,
        macd_signal=3,
        momentum_window=3,
    )
    X, y = fb.build(prices)
    assert X.shape[0] == y.shape[0]
    assert X.shape[1] == 10  # 3 returns + 7 engineered features


def test_simple_model_fit_predict():
    # linear relationship y = 2*x1 + noise
    rng = np.random.RandomState(0)
    X = rng.normal(size=(100, 3))
    coef = np.array([2.0, 0.0, 0.0])
    y = X @ coef + rng.normal(scale=0.1, size=(100,))
    m = SimpleModelWrapper(alpha=1.0)
    m.fit(X, y)
    preds = m.predict(X[:5])
    assert preds.shape[0] == 5
