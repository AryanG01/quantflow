"""Live slippage estimation."""

from __future__ import annotations

from collections import deque


class LiveSlippageEstimator:
    """Estimate live slippage from filled orders vs expected prices."""

    def __init__(self, window: int = 100) -> None:
        self._slippages: deque[float] = deque(maxlen=window)

    def record(self, expected_price: float, fill_price: float) -> None:
        """Record a fill for slippage calculation."""
        if expected_price > 0:
            slippage_bps = abs(fill_price - expected_price) / expected_price * 10_000
            self._slippages.append(slippage_bps)

    @property
    def mean_slippage_bps(self) -> float:
        if not self._slippages:
            return 0.0
        return sum(self._slippages) / len(self._slippages)

    @property
    def p95_slippage_bps(self) -> float:
        if not self._slippages:
            return 0.0
        sorted_slippage = sorted(self._slippages)
        idx = int(len(sorted_slippage) * 0.95)
        return sorted_slippage[min(idx, len(sorted_slippage) - 1)]
