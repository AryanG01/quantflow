"""Tests for volatility-targeted position sizing."""

from __future__ import annotations

from datetime import UTC, datetime

from packages.common.types import Direction, PortfolioSnapshot, Regime, Signal
from packages.risk.position_sizer import VolTargetPositionSizer


def _make_signal(strength: float = 0.5, confidence: float = 0.8) -> Signal:
    return Signal(
        time=datetime.now(UTC),
        symbol="BTC/USDT",
        direction=Direction.LONG,
        strength=strength,
        confidence=confidence,
        regime=Regime.TRENDING,
    )


def _make_portfolio(equity: float = 100_000.0) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        time=datetime.now(UTC),
        equity=equity,
        cash=equity,
        positions_value=0.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        drawdown_pct=0.0,
    )


class TestPositionSizer:
    def test_high_vol_smaller_position(self) -> None:
        """Higher volatility should result in smaller position."""
        sizer = VolTargetPositionSizer(vol_target=0.15, max_position_pct=0.25)
        signal = _make_signal(strength=0.5, confidence=1.0)
        portfolio = _make_portfolio()

        low_vol_size = sizer.compute_size(signal, portfolio, 50000.0, realized_vol=0.10)
        high_vol_size = sizer.compute_size(signal, portfolio, 50000.0, realized_vol=0.50)

        assert high_vol_size < low_vol_size

    def test_cap_at_max_position(self) -> None:
        """Position should be capped at max_position_pct."""
        sizer = VolTargetPositionSizer(vol_target=0.15, max_position_pct=0.25)
        signal = _make_signal(strength=1.0, confidence=1.0)
        portfolio = _make_portfolio(equity=100_000.0)

        # Very low vol → would want huge position → cap should apply
        size = sizer.compute_size(signal, portfolio, 50000.0, realized_vol=0.01)

        max_value = 0.25 * 100_000  # 25K
        max_qty = max_value / 50000.0  # 0.5 BTC
        assert size <= max_qty + 1e-10

    def test_zero_vol_returns_zero(self) -> None:
        """Zero volatility should return zero position (avoid div by zero)."""
        sizer = VolTargetPositionSizer()
        size = sizer.compute_size(_make_signal(), _make_portfolio(), 50000.0, realized_vol=0.0)
        assert size == 0.0

    def test_confidence_scales_position(self) -> None:
        """Higher confidence should produce larger position."""
        sizer = VolTargetPositionSizer()
        portfolio = _make_portfolio()

        high_conf = sizer.compute_size(
            _make_signal(confidence=0.9), portfolio, 50000.0, realized_vol=0.20
        )
        low_conf = sizer.compute_size(
            _make_signal(confidence=0.3), portfolio, 50000.0, realized_vol=0.20
        )

        assert high_conf > low_conf

    def test_strength_scales_position(self) -> None:
        """Stronger signal should produce larger position."""
        sizer = VolTargetPositionSizer()
        portfolio = _make_portfolio()

        strong = sizer.compute_size(
            _make_signal(strength=0.9), portfolio, 50000.0, realized_vol=0.20
        )
        weak = sizer.compute_size(
            _make_signal(strength=0.1), portfolio, 50000.0, realized_vol=0.20
        )

        assert strong > weak
