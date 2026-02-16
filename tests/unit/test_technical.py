"""Tests for technical feature computation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from packages.features.technical import TechnicalFeatures


def _make_candles(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    prices = 100 * np.cumprod(1 + np.random.normal(0.0005, 0.02, n))
    return pd.DataFrame(
        {
            "time": pd.date_range("2023-01-01", periods=n, freq="4h", tz="UTC"),
            "open": prices * (1 - np.random.uniform(0, 0.005, n)),
            "high": prices * (1 + np.random.uniform(0, 0.01, n)),
            "low": prices * (1 - np.random.uniform(0, 0.01, n)),
            "close": prices,
            "volume": np.random.uniform(100, 1000, n),
        }
    )


class TestTechnicalFeatures:
    def test_rsi_range(self) -> None:
        """RSI should be in [0, 100] after warmup."""
        candles = _make_candles()
        features = TechnicalFeatures().compute(candles)

        rsi = features["rsi"].dropna()
        assert len(rsi) > 0
        assert rsi.min() >= 0
        assert rsi.max() <= 100

    def test_no_nan_after_warmup(self) -> None:
        """After warmup period, no features should be NaN."""
        candles = _make_candles(n=300)
        features = TechnicalFeatures(vol_window=24).compute(candles)

        # After bar 50 (max warmup), no NaN
        after_warmup = features.iloc[50:]
        for col in features.columns:
            nan_count = after_warmup[col].isna().sum()
            assert nan_count == 0, f"Column {col} has {nan_count} NaN values after warmup"

    def test_atr_positive(self) -> None:
        """ATR should always be positive."""
        candles = _make_candles()
        features = TechnicalFeatures().compute(candles)

        atr = features["atr"].dropna()
        assert (atr > 0).all()

    def test_log_returns_reasonable(self) -> None:
        """Log returns should be small for typical price data."""
        candles = _make_candles()
        features = TechnicalFeatures().compute(candles)

        log_ret = features["log_returns"].dropna()
        assert log_ret.abs().max() < 1.0  # no 100% moves in synthetic data

    def test_realized_vol_positive(self) -> None:
        """Realized volatility should be positive."""
        candles = _make_candles()
        features = TechnicalFeatures().compute(candles)

        vol = features["realized_vol"].dropna()
        assert (vol > 0).all()

    def test_feature_names_match_columns(self) -> None:
        """feature_names() should match actual output columns."""
        tf = TechnicalFeatures()
        candles = _make_candles()
        features = tf.compute(candles)

        assert set(tf.feature_names()) == set(features.columns)
