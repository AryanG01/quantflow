"""Tests for backtest metrics computation."""

from __future__ import annotations

import numpy as np
import pytest

from packages.backtest.metrics import (
    compute_hit_rate,
    compute_max_drawdown,
    compute_profit_factor,
    compute_sharpe,
    compute_sortino,
)


class TestSharpe:
    def test_positive_returns_positive_sharpe(self) -> None:
        returns = np.array([0.01, 0.02, 0.01, 0.015, 0.005])
        assert compute_sharpe(returns) > 0

    def test_negative_returns_negative_sharpe(self) -> None:
        returns = np.array([-0.01, -0.02, -0.01, -0.015, -0.005])
        assert compute_sharpe(returns) < 0

    def test_zero_std_returns_zero(self) -> None:
        returns = np.array([0.0, 0.0, 0.0])
        assert compute_sharpe(returns) == 0.0

    def test_empty_returns_zero(self) -> None:
        assert compute_sharpe(np.array([])) == 0.0


class TestSortino:
    def test_only_positive_returns_zero_downside(self) -> None:
        """All positive returns → no downside deviation → 0."""
        returns = np.array([0.01, 0.02, 0.03])
        assert compute_sortino(returns) == 0.0

    def test_mixed_returns(self) -> None:
        returns = np.array([0.01, -0.005, 0.02, -0.01, 0.015])
        sortino = compute_sortino(returns)
        sharpe = compute_sharpe(returns)
        # Sortino should be >= Sharpe when there's positive skew
        assert sortino >= sharpe or abs(sortino - sharpe) < 0.01


class TestMaxDrawdown:
    def test_monotonic_increase_zero_dd(self) -> None:
        equity = np.array([100.0, 110.0, 120.0, 130.0])
        dd, duration = compute_max_drawdown(equity)
        assert dd == pytest.approx(0.0)
        assert duration == 0

    def test_known_drawdown(self) -> None:
        # Peak at 200, trough at 160 → 20% drawdown
        equity = np.array([100.0, 150.0, 200.0, 160.0, 180.0, 210.0])
        dd, _ = compute_max_drawdown(equity)
        assert dd == pytest.approx(0.2)

    def test_drawdown_duration(self) -> None:
        # Below peak for 3 bars
        equity = np.array([100.0, 200.0, 190.0, 180.0, 195.0, 210.0])
        _, duration = compute_max_drawdown(equity)
        assert duration == 3

    def test_empty_equity(self) -> None:
        dd, duration = compute_max_drawdown(np.array([]))
        assert dd == 0.0
        assert duration == 0


class TestHitRate:
    def test_all_winners(self) -> None:
        assert compute_hit_rate(np.array([0.01, 0.02, 0.005])) == pytest.approx(1.0)

    def test_all_losers(self) -> None:
        assert compute_hit_rate(np.array([-0.01, -0.02])) == pytest.approx(0.0)

    def test_fifty_fifty(self) -> None:
        assert compute_hit_rate(np.array([0.01, -0.01])) == pytest.approx(0.5)

    def test_empty(self) -> None:
        assert compute_hit_rate(np.array([])) == 0.0


class TestProfitFactor:
    def test_all_gains(self) -> None:
        assert compute_profit_factor(np.array([0.01, 0.02])) == float("inf")

    def test_all_losses(self) -> None:
        assert compute_profit_factor(np.array([-0.01, -0.02])) == 0.0

    def test_known_ratio(self) -> None:
        # gains=0.03, losses=0.01 → PF=3.0
        trades = np.array([0.02, 0.01, -0.01])
        assert compute_profit_factor(trades) == pytest.approx(3.0)
