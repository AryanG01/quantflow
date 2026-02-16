"""Volatility-targeted position sizing with uncertainty scaling.

Position size formula:
    raw_size = (vol_target / realized_vol) * |signal.strength|
    sized = raw_size * confidence
    capped = min(sized, max_position_pct)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packages.common.types import PortfolioSnapshot, Signal


class VolTargetPositionSizer:
    """Volatility-targeted position sizer."""

    def __init__(
        self,
        vol_target: float = 0.15,
        max_position_pct: float = 0.25,
    ) -> None:
        self._vol_target = vol_target
        self._max_position_pct = max_position_pct

    def compute_size(
        self,
        signal: Signal,
        portfolio: PortfolioSnapshot,
        current_price: float,
        realized_vol: float,
    ) -> float:
        """Compute position size in base currency units.

        Args:
            signal: Trading signal with strength and confidence
            portfolio: Current portfolio state
            current_price: Current asset price
            realized_vol: Current annualized realized volatility

        Returns:
            Position size in base units (e.g., BTC quantity)
        """
        if realized_vol <= 0 or current_price <= 0 or portfolio.equity <= 0:
            return 0.0

        # Vol-targeted raw size as fraction of equity
        vol_ratio = self._vol_target / realized_vol
        raw_pct = vol_ratio * abs(signal.strength)

        # Scale by model confidence
        sized_pct = raw_pct * signal.confidence

        # Cap at maximum position
        capped_pct = min(sized_pct, self._max_position_pct)

        # Convert to dollar value, then to base units
        dollar_value = capped_pct * portfolio.equity
        quantity = dollar_value / current_price

        return quantity
