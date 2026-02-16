"""Running drawdown monitoring with kill switch trigger."""

from __future__ import annotations

from packages.common.logging import get_logger

logger = get_logger(__name__)


class DrawdownMonitor:
    """Track running peak-to-trough drawdown."""

    def __init__(self, max_drawdown_pct: float = 0.15) -> None:
        self._max_drawdown_pct = max_drawdown_pct
        self._peak_equity: float = 0.0
        self._current_drawdown: float = 0.0

    def update(self, equity: float) -> float:
        """Update with new equity value.

        Args:
            equity: Current portfolio equity

        Returns:
            Current drawdown as a positive fraction (0.10 = 10% drawdown)
        """
        if equity > self._peak_equity:
            self._peak_equity = equity

        if self._peak_equity > 0:
            self._current_drawdown = (self._peak_equity - equity) / self._peak_equity
        else:
            self._current_drawdown = 0.0

        return self._current_drawdown

    def should_trigger_kill_switch(self) -> bool:
        """Check if drawdown exceeds the kill switch threshold."""
        return self._current_drawdown >= self._max_drawdown_pct

    @property
    def current_drawdown(self) -> float:
        return self._current_drawdown

    @property
    def peak_equity(self) -> float:
        return self._peak_equity
