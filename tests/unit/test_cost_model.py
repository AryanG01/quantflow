"""Tests for the transaction cost model."""

from __future__ import annotations

import numpy as np
import pytest

from packages.backtest.cost_model import CostModel, CostModelConfig


class TestCostModel:
    def test_zero_trade_returns_fixed_costs(self) -> None:
        """Zero trade value should only incur fixed spread + fees."""
        model = CostModel(
            CostModelConfig(fixed_spread_bps=5.0, linear_impact_bps=2.0, taker_fee_bps=10.0)
        )
        trades = np.array([0.0])
        adv = np.array([1_000_000.0])

        costs = model.compute_costs_bps(trades, adv)
        # fixed_spread(5) + linear_impact(2) * 0/1M + taker_fee(10) = 15
        assert costs[0] == pytest.approx(15.0)

    def test_larger_trade_has_higher_cost(self) -> None:
        """Linear impact should increase with trade size relative to ADV."""
        model = CostModel(
            CostModelConfig(fixed_spread_bps=5.0, linear_impact_bps=2.0, taker_fee_bps=10.0)
        )
        small_trade = np.array([1_000.0])
        large_trade = np.array([100_000.0])
        adv = np.array([1_000_000.0])

        small_cost = model.compute_costs_bps(small_trade, adv)
        large_cost = model.compute_costs_bps(large_trade, adv)

        assert large_cost[0] > small_cost[0]

    def test_costs_pct_conversion(self) -> None:
        """compute_costs_pct should be compute_costs_bps / 10000."""
        model = CostModel()
        trades = np.array([10_000.0])
        adv = np.array([1_000_000.0])

        bps = model.compute_costs_bps(trades, adv)
        pct = model.compute_costs_pct(trades, adv)

        assert pct[0] == pytest.approx(bps[0] / 10_000.0)

    def test_zero_adv_no_division_error(self) -> None:
        """Zero ADV should not cause division by zero."""
        model = CostModel()
        trades = np.array([1_000.0])
        adv = np.array([0.0])

        costs = model.compute_costs_bps(trades, adv)
        assert np.isfinite(costs[0])

    def test_vectorized_computation(self) -> None:
        """Should handle arrays of multiple trades."""
        model = CostModel()
        trades = np.array([1_000.0, 5_000.0, 10_000.0])
        adv = np.array([1_000_000.0, 500_000.0, 2_000_000.0])

        costs = model.compute_costs_bps(trades, adv)
        assert len(costs) == 3
        assert all(np.isfinite(costs))
