"""Tests for pre-trade risk checks and kill switch."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from packages.common.errors import KillSwitchError
from packages.common.types import Direction, PortfolioSnapshot, Regime, Signal
from packages.risk.risk_checks import RiskChecker


def _make_portfolio(drawdown: float = 0.0, equity: float = 100_000.0) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        time=datetime.now(UTC),
        equity=equity,
        cash=equity,
        positions_value=0.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        drawdown_pct=drawdown,
    )


def _make_signal() -> Signal:
    return Signal(
        time=datetime.now(UTC),
        symbol="BTC/USDT",
        direction=Direction.LONG,
        strength=0.5,
        confidence=0.8,
        regime=Regime.TRENDING,
    )


class TestRiskChecks:
    def test_all_checks_pass_normal_conditions(self) -> None:
        """Normal trade should pass all checks."""
        checker = RiskChecker(max_drawdown_pct=0.15)
        approved, reason = checker.check_pre_trade(
            _make_signal(), _make_portfolio(), trade_value_usd=5000.0
        )
        assert approved
        assert "passed" in reason.lower()

    def test_kill_switch_at_16pct_drawdown(self) -> None:
        """16% drawdown should trigger kill switch (threshold 15%)."""
        checker = RiskChecker(max_drawdown_pct=0.15)
        with pytest.raises(KillSwitchError):
            checker.check_pre_trade(
                _make_signal(), _make_portfolio(drawdown=0.16), trade_value_usd=5000.0
            )
        assert checker.kill_switch_active

    def test_concentration_30pct_rejected(self) -> None:
        """Trade exceeding 30% concentration should be rejected."""
        checker = RiskChecker(max_concentration_pct=0.30)
        approved, reason = checker.check_pre_trade(
            _make_signal(), _make_portfolio(equity=100_000.0), trade_value_usd=35_000.0
        )
        assert not approved
        assert "concentration" in reason.lower()

    def test_below_minimum_trade_rejected(self) -> None:
        """Trade below minimum size should be rejected."""
        checker = RiskChecker(min_trade_usd=10.0)
        approved, reason = checker.check_pre_trade(
            _make_signal(), _make_portfolio(), trade_value_usd=5.0
        )
        assert not approved
        assert "minimum" in reason.lower()

    def test_stale_data_rejected(self) -> None:
        """Stale data should be rejected."""
        checker = RiskChecker(staleness_threshold_minutes=30)
        old_time = datetime.now(UTC) - timedelta(minutes=45)
        approved, reason = checker.check_pre_trade(
            _make_signal(), _make_portfolio(), trade_value_usd=5000.0, data_timestamp=old_time
        )
        assert not approved
        assert "stale" in reason.lower() or "old" in reason.lower()

    def test_kill_switch_blocks_all_trades(self) -> None:
        """Once kill switch activates, all subsequent trades are blocked."""
        checker = RiskChecker(max_drawdown_pct=0.15)

        # Trigger kill switch
        with pytest.raises(KillSwitchError):
            checker.check_pre_trade(
                _make_signal(), _make_portfolio(drawdown=0.20), trade_value_usd=5000.0
            )

        # Now even a normal trade should be blocked
        approved, reason = checker.check_pre_trade(
            _make_signal(), _make_portfolio(drawdown=0.0), trade_value_usd=1000.0
        )
        assert not approved
        assert "kill switch" in reason.lower()

    def test_reset_kill_switch(self) -> None:
        """After reset, trades should be allowed again."""
        checker = RiskChecker(max_drawdown_pct=0.15)

        with pytest.raises(KillSwitchError):
            checker.check_pre_trade(
                _make_signal(), _make_portfolio(drawdown=0.20), trade_value_usd=5000.0
            )

        checker.reset_kill_switch()

        approved, _ = checker.check_pre_trade(
            _make_signal(), _make_portfolio(drawdown=0.0), trade_value_usd=1000.0
        )
        assert approved
