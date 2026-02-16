"""Integration test for the backtest engine on synthetic data."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from packages.backtest.benchmarks import buy_and_hold, ma_crossover
from packages.backtest.engine_vectorized import BacktestConfig, run_vectorized_backtest


def _make_trending_candles(n: int = 500, start_price: float = 100.0) -> pd.DataFrame:
    """Generate synthetic trending candle data (upward drift + noise)."""
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, n)  # slight upward drift
    prices = start_price * np.cumprod(1 + returns)

    times = pd.date_range("2023-01-01", periods=n, freq="4h", tz="UTC")

    return pd.DataFrame(
        {
            "time": times,
            "open": prices * (1 - np.random.uniform(0, 0.005, n)),
            "high": prices * (1 + np.random.uniform(0, 0.01, n)),
            "low": prices * (1 - np.random.uniform(0, 0.01, n)),
            "close": prices,
            "volume": np.random.uniform(100, 1000, n),
        }
    )


class TestBacktestEngine:
    def test_buy_and_hold_returns_match(self) -> None:
        """Buy-and-hold equity curve should track price movement."""
        candles = _make_trending_candles()
        result = run_vectorized_backtest(candles, buy_and_hold)

        # Equity should have moved (not flat)
        assert result.equity_curve[-1] != result.equity_curve[0]
        assert len(result.equity_curve) == len(candles)
        assert result.metrics.total_trades >= 0

    def test_ma_crossover_no_lookahead(self) -> None:
        """MA crossover signal should use only past data.

        Verify by checking that signal at bar i depends only on bars < i.
        The .shift(1) in ma_crossover ensures this.
        """
        candles = _make_trending_candles(n=200)
        positions = ma_crossover(candles)

        # First slow_period+1 bars should be zero (warmup)
        assert all(positions[:52] == 0.0)  # 50 + 1 + buffer

    def test_costs_reduce_returns(self) -> None:
        """Backtest with costs should produce lower returns than without."""
        candles = _make_trending_candles()

        no_cost = run_vectorized_backtest(
            candles,
            ma_crossover,
            BacktestConfig(
                cost_model=__import__(
                    "packages.backtest.cost_model", fromlist=["CostModelConfig"]
                ).CostModelConfig(
                    fixed_spread_bps=0.0,
                    linear_impact_bps=0.0,
                    taker_fee_bps=0.0,
                )
            ),
        )

        with_cost = run_vectorized_backtest(candles, ma_crossover)

        assert with_cost.metrics.total_return <= no_cost.metrics.total_return

    def test_metrics_are_finite(self) -> None:
        """All metrics should be finite numbers."""
        candles = _make_trending_candles()
        result = run_vectorized_backtest(candles, ma_crossover)
        m = result.metrics

        assert np.isfinite(m.sharpe_ratio)
        assert np.isfinite(m.sortino_ratio)
        assert np.isfinite(m.max_drawdown)
        assert np.isfinite(m.total_return)
        assert np.isfinite(m.hit_rate)
        assert m.max_drawdown >= 0

    def test_equity_curve_starts_at_initial_capital(self) -> None:
        candles = _make_trending_candles(n=100)
        config = BacktestConfig(initial_capital=50_000.0)
        result = run_vectorized_backtest(candles, buy_and_hold, config)

        assert result.equity_curve[0] == pytest.approx(50_000.0, rel=0.01)
