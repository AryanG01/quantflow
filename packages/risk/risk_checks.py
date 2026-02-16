"""Pre-trade and post-trade risk checks.

Safety-critical: bugs here = financial loss.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from packages.common.errors import KillSwitchError
from packages.common.logging import get_logger

if TYPE_CHECKING:
    from packages.common.types import PortfolioSnapshot, Signal

logger = get_logger(__name__)


class RiskChecker:
    """Pre-trade and post-trade risk validation."""

    def __init__(
        self,
        max_drawdown_pct: float = 0.15,
        max_concentration_pct: float = 0.30,
        max_position_pct: float = 0.25,
        min_trade_usd: float = 10.0,
        staleness_threshold_minutes: int = 30,
    ) -> None:
        self._max_drawdown_pct = max_drawdown_pct
        self._max_concentration_pct = max_concentration_pct
        self._max_position_pct = max_position_pct
        self._min_trade_usd = min_trade_usd
        self._staleness_threshold_minutes = staleness_threshold_minutes
        self._kill_switch_active = False

    def check_pre_trade(
        self,
        signal: Signal,
        portfolio: PortfolioSnapshot,
        trade_value_usd: float,
        data_timestamp: datetime | None = None,
    ) -> tuple[bool, str]:
        """Run all pre-trade risk checks.

        Returns:
            (approved, reason) — False + reason if any check fails
        """
        # Kill switch check (most critical — check first)
        if self._kill_switch_active:
            return False, "Kill switch is active — all trading halted"

        if portfolio.drawdown_pct >= self._max_drawdown_pct:
            self._kill_switch_active = True
            logger.critical(
                "kill_switch_triggered",
                drawdown_pct=portfolio.drawdown_pct,
                threshold=self._max_drawdown_pct,
            )
            raise KillSwitchError(
                f"Max drawdown {portfolio.drawdown_pct:.1%} >= "
                f"threshold {self._max_drawdown_pct:.1%}"
            )

        # Minimum trade size
        if trade_value_usd < self._min_trade_usd:
            return False, f"Trade value ${trade_value_usd:.2f} below minimum ${self._min_trade_usd}"

        # Concentration check
        if portfolio.equity > 0:
            concentration = trade_value_usd / portfolio.equity
            if concentration > self._max_concentration_pct:
                return False, (
                    f"Concentration {concentration:.1%} exceeds "
                    f"max {self._max_concentration_pct:.1%}"
                )

        # Position size check
        if portfolio.equity > 0:
            position_pct = trade_value_usd / portfolio.equity
            if position_pct > self._max_position_pct:
                return False, (
                    f"Position {position_pct:.1%} exceeds max {self._max_position_pct:.1%}"
                )

        # Staleness check
        if data_timestamp is not None:
            age_minutes = (datetime.now(UTC) - data_timestamp).total_seconds() / 60
            if age_minutes > self._staleness_threshold_minutes:
                return False, (
                    f"Data is {age_minutes:.0f} min old, "
                    f"exceeds {self._staleness_threshold_minutes} min threshold"
                )

        return True, "All checks passed"

    def check_post_trade(self, portfolio: PortfolioSnapshot) -> tuple[bool, str]:
        """Post-trade risk validation."""
        if portfolio.drawdown_pct >= self._max_drawdown_pct:
            self._kill_switch_active = True
            return False, "Post-trade drawdown exceeds limit"
        return True, "Post-trade checks passed"

    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch_active

    def reset_kill_switch(self) -> None:
        """Manually reset the kill switch (requires human decision)."""
        logger.warning("kill_switch_reset")
        self._kill_switch_active = False
