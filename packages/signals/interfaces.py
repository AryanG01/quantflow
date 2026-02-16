"""Abstract interfaces for signal generation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from packages.common.types import Regime, Signal


class SignalCombiner(ABC):
    """Abstract base class for signal fusion/combination."""

    @abstractmethod
    def combine(
        self,
        components: dict[str, float],
        regime: Regime,
        confidence: float,
        symbol: str,
    ) -> Signal:
        """Combine component signals into a final signal.

        Args:
            components: Dict of signal component scores (e.g., {"technical": 0.5, "ml": 0.3})
            regime: Current market regime
            confidence: Model confidence (0-1)
            symbol: Trading symbol

        Returns:
            Combined Signal
        """
