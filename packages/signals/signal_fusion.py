"""Regime-gated Mixture-of-Experts signal fusion.

The core differentiator: regime determines which signal components
get which weights. Choppy regime also scales down position size.

All defaults live in SignalFusionConfig (packages/common/config.py) —
there is no secondary DEFAULT_REGIME_WEIGHTS dict here.
"""

from __future__ import annotations

from datetime import UTC, datetime

from packages.common.config import RegimeWeights, SignalFusionConfig
from packages.common.types import Direction, Regime, Signal
from packages.signals.interfaces import SignalCombiner


class RegimeGatedMoE(SignalCombiner):
    """Regime-gated Mixture-of-Experts signal combiner.

    In each regime, different signal components get different weights:
    - Trending: heavy on ML and technical
    - Mean-reverting: heavy on technical
    - Choppy: reduced overall position + more sentiment weight
    """

    def __init__(self, config: SignalFusionConfig | None = None) -> None:
        cfg = config or SignalFusionConfig()
        self._weights = cfg.regime_weights
        self._choppy_scale = cfg.choppy_scale
        self._direction_threshold = cfg.direction_threshold

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
        # Fall back to choppy weights when regime key is missing
        fallback = self._weights.get(
            "choppy", RegimeWeights(technical=0.33, ml=0.34, sentiment=0.33)
        )
        weights = self._weights.get(regime.value, fallback)

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

        # Determine direction from config-driven threshold
        if strength > self._direction_threshold:
            direction = Direction.LONG
        elif strength < -self._direction_threshold:
            direction = Direction.SHORT
        else:
            direction = Direction.FLAT

        return Signal(
            time=datetime.now(UTC),
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            regime=regime,
            components=components,
        )
