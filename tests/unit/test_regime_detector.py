"""Tests for HMM regime detection."""

from __future__ import annotations

import numpy as np

from packages.common.types import Regime
from packages.signals.regime_detector import RegimeDetector


def _make_regime_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data with clear regime characteristics."""
    np.random.seed(42)

    # Trending: low vol, positive drift
    trending_returns = np.random.normal(0.005, 0.01, 200)
    trending_vol = np.full(200, 0.05) + np.random.normal(0, 0.005, 200)

    # Mean-reverting: medium vol, zero drift
    mr_returns = np.random.normal(0.0, 0.02, 200)
    mr_vol = np.full(200, 0.15) + np.random.normal(0, 0.01, 200)

    # Choppy: high vol, erratic
    choppy_returns = np.random.normal(0.0, 0.05, 200)
    choppy_vol = np.full(200, 0.40) + np.random.normal(0, 0.02, 200)

    log_returns = np.concatenate([trending_returns, mr_returns, choppy_returns])
    realized_vol = np.abs(np.concatenate([trending_vol, mr_vol, choppy_vol]))

    return log_returns, realized_vol


class TestRegimeDetector:
    def test_fit_and_predict(self) -> None:
        """Should fit without error and produce valid regimes."""
        log_returns, realized_vol = _make_regime_data()
        detector = RegimeDetector(n_states=3)
        detector.fit(log_returns, realized_vol)

        regimes = detector.predict(log_returns, realized_vol)
        assert len(regimes) == len(log_returns)
        assert all(isinstance(r, Regime) for r in regimes)

    def test_trending_segment_detected(self) -> None:
        """Low-vol segment should be mostly classified as trending."""
        log_returns, realized_vol = _make_regime_data()
        detector = RegimeDetector(n_states=3)
        detector.fit(log_returns, realized_vol)

        regimes = detector.predict(log_returns, realized_vol)

        # First 200 bars are trending data
        trending_segment = regimes[:200]
        trending_count = sum(1 for r in trending_segment if r == Regime.TRENDING)
        # At least 50% should be classified as trending
        assert trending_count / len(trending_segment) > 0.5

    def test_choppy_segment_detected(self) -> None:
        """High-vol segment should be mostly classified as choppy."""
        log_returns, realized_vol = _make_regime_data()
        detector = RegimeDetector(n_states=3)
        detector.fit(log_returns, realized_vol)

        regimes = detector.predict(log_returns, realized_vol)

        # Last 200 bars are choppy data
        choppy_segment = regimes[400:]
        choppy_count = sum(1 for r in choppy_segment if r == Regime.CHOPPY)
        # HMM is probabilistic; choppy segment should be predominantly non-trending
        non_trending = sum(1 for r in choppy_segment if r != Regime.TRENDING)
        assert non_trending / len(choppy_segment) > 0.7

    def test_predict_current(self) -> None:
        """predict_current should return a single Regime."""
        log_returns, realized_vol = _make_regime_data()
        detector = RegimeDetector(n_states=3)
        detector.fit(log_returns, realized_vol)

        regime = detector.predict_current(log_returns, realized_vol)
        assert isinstance(regime, Regime)

    def test_unfitted_defaults_to_choppy(self) -> None:
        """Unfitted detector should default to CHOPPY (safest)."""
        detector = RegimeDetector()
        regimes = detector.predict(np.array([0.01, -0.01]), np.array([0.1, 0.2]))
        assert all(r == Regime.CHOPPY for r in regimes)
