"""Realistic fill simulation for event-driven backtesting.

Simulates partial fills, latency, spread crossing, and cancellations.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class FillSimulationConfig:
    """Configuration for realistic fill simulation."""

    latency_min_ms: int = 100
    latency_max_ms: int = 2000
    partial_fill_min_pct: float = 0.5
    spread_bps: float = 5.0
    cancel_after_bars: int = 3


class FillSimulator:
    """Simulate realistic order fills."""

    def __init__(self, config: FillSimulationConfig | None = None) -> None:
        self._config = config or FillSimulationConfig()
        self._rng = np.random.default_rng(42)

    def simulate_latency_bars(self, timeframe_seconds: int = 14400) -> int:
        """Simulate fill latency as number of bars delay.

        For 4h bars, typical latency < 1 bar, so most fills are immediate.
        """
        latency_ms = self._rng.uniform(
            self._config.latency_min_ms, self._config.latency_max_ms
        )
        latency_bars = latency_ms / 1000 / timeframe_seconds
        return int(np.ceil(latency_bars))

    def simulate_fill_quantity(self, order_qty: float, bar_volume: float) -> float:
        """Simulate partial fill based on volume.

        Fill rate depends on order size relative to bar volume.
        """
        if bar_volume <= 0:
            return 0.0

        # Volume-proportional fill rate
        volume_ratio = min(order_qty / bar_volume, 1.0)

        if volume_ratio > 0.1:
            # Large order relative to volume → partial fill
            fill_pct = self._rng.uniform(self._config.partial_fill_min_pct, 1.0)
        else:
            # Small order → full fill
            fill_pct = 1.0

        return order_qty * fill_pct

    def simulate_fill_price(self, mid_price: float, is_buy: bool) -> float:
        """Simulate fill price with spread crossing."""
        half_spread_pct = self._config.spread_bps / 10_000 / 2

        if is_buy:
            return mid_price * (1 + half_spread_pct)
        else:
            return mid_price * (1 - half_spread_pct)
