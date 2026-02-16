"""Tests for regime-gated MoE signal fusion."""

from __future__ import annotations

from packages.common.types import Direction, Regime
from packages.signals.signal_fusion import RegimeGatedMoE


class TestSignalFusion:
    def test_known_weights_produce_expected_output(self) -> None:
        """With known inputs and weights, output should be deterministic."""
        fusioner = RegimeGatedMoE()
        components = {"technical": 0.8, "ml": 0.6, "sentiment": 0.2}

        signal = fusioner.combine(
            components=components,
            regime=Regime.TRENDING,
            confidence=1.0,
            symbol="BTC/USDT",
        )

        # trending weights: tech=0.4, ml=0.5, sentiment=0.1
        expected = 0.4 * 0.8 + 0.5 * 0.6 + 0.1 * 0.2  # = 0.32 + 0.30 + 0.02 = 0.64
        assert abs(signal.strength - expected) < 0.01
        assert signal.direction == Direction.LONG

    def test_choppy_regime_scales_down(self) -> None:
        """Choppy regime should reduce signal strength."""
        fusioner = RegimeGatedMoE()
        components = {"technical": 0.8, "ml": 0.6, "sentiment": 0.2}

        trending_signal = fusioner.combine(
            components, Regime.TRENDING, confidence=1.0, symbol="BTC/USDT"
        )
        choppy_signal = fusioner.combine(
            components, Regime.CHOPPY, confidence=1.0, symbol="BTC/USDT"
        )

        assert abs(choppy_signal.strength) < abs(trending_signal.strength)

    def test_low_confidence_reduces_strength(self) -> None:
        """Low confidence should reduce final signal strength."""
        fusioner = RegimeGatedMoE()
        components = {"technical": 0.8, "ml": 0.6, "sentiment": 0.2}

        high_conf = fusioner.combine(
            components, Regime.TRENDING, confidence=1.0, symbol="BTC/USDT"
        )
        low_conf = fusioner.combine(
            components, Regime.TRENDING, confidence=0.3, symbol="BTC/USDT"
        )

        assert abs(low_conf.strength) < abs(high_conf.strength)

    def test_zero_strength_is_flat(self) -> None:
        """Near-zero signal should be classified as FLAT."""
        fusioner = RegimeGatedMoE()
        components = {"technical": 0.0, "ml": 0.0, "sentiment": 0.0}

        signal = fusioner.combine(
            components, Regime.TRENDING, confidence=1.0, symbol="BTC/USDT"
        )
        assert signal.direction == Direction.FLAT

    def test_negative_components_go_short(self) -> None:
        """Negative component signals should produce SHORT direction."""
        fusioner = RegimeGatedMoE()
        components = {"technical": -0.8, "ml": -0.6, "sentiment": -0.2}

        signal = fusioner.combine(
            components, Regime.TRENDING, confidence=1.0, symbol="BTC/USDT"
        )
        assert signal.direction == Direction.SHORT
        assert signal.strength < 0
