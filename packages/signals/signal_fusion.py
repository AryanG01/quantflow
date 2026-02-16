"""Regime-gated Mixture-of-Experts signal fusion.

The core differentiator: regime determines which signal components
get which weights. Choppy regime also scales down position size.
"""

from __future__ import annotations

from datetime import datetime, timezone

from packages.common.config import RegimeWeights, SignalFusionConfig
from packages.common.types import Direction, Regime, Signal
from packages.signals.interfaces import SignalCombiner

DEFAULT_REGIME_WEIGHTS: dict[str, RegimeWeights] = {
    "trending": RegimeWeights(technical=0.4, ml=0.5, sentiment=0.1),
    "mean_reverting": RegimeWeights(technical=0.5, ml=0.3, sentiment=0.2),
    "choppy": RegimeWeights(technical=0.3, ml=0.3, sentiment=0.4),
}


class RegimeGatedMoE(SignalCombiner):
    """Regime-gated Mixture-of-Experts signal combiner.

    In each regime, different signal components get different weights:
    - Trending: heavy on ML and technical
    - Mean-reverting: heavy on technical
    - Choppy: reduced overall position + more sentiment weight
    """

    def __init__(self, config: SignalFusionConfig | None = None) -> None:
        if config and config.regime_weights:
            self._weights = config.regime_weights
        else:
            self._weights = DEFAULT_REGIME_WEIGHTS
        self._choppy_scale = config.choppy_scale if config else 0.3

    def combine(
        self,
        components: dict[str, float],
        regime: Regime,
        confidence: float,
        symbol: str,
    ) -> Signal:
        """Combine signals using regime-dependent weights.

        Args:
            components: Signal scores per component (e.g., {"technical": 0.6, "ml": 0.3})
            regime: Current market regime
            confidence: Model confidence [0, 1]
            symbol: Trading symbol

        Returns:
            Combined Signal with direction, strength, and confidence
        """
        weights = self._weights.get(regime.value, DEFAULT_REGIME_WEIGHTS["choppy"])

        # Weighted sum of components
        raw_strength = (
            weights.technical * components.get("technical", 0.0)
            + weights.ml * components.get("ml", 0.0)
            + weights.sentiment * components.get("sentiment", 0.0)
        )

        # Apply choppy regime scaling
        if regime == Regime.CHOPPY:
            raw_strength *= self._choppy_scale

        # Scale by confidence
        strength = raw_strength * confidence

        # Clamp to [-1, 1]
        strength = max(-1.0, min(1.0, strength))

        # Determine direction
        if strength > 0.05:
            direction = Direction.LONG
        elif strength < -0.05:
            direction = Direction.SHORT
        else:
            direction = Direction.FLAT

        return Signal(
            time=datetime.now(timezone.utc),
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            regime=regime,
            components=components,
        )
