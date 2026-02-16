"""Ablation study: compare full system vs component removals."""

from __future__ import annotations

import numpy as np
import pandas as pd

from packages.backtest.benchmarks import buy_and_hold, ma_crossover
from packages.backtest.engine_vectorized import BacktestConfig, run_vectorized_backtest
from packages.backtest.report import print_report


def run_ablation(candles: pd.DataFrame) -> None:
    """Run ablation study comparing strategy variants."""
    config = BacktestConfig(initial_capital=100_000.0)

    variants = {
        "Buy & Hold": buy_and_hold,
        "MA Crossover (baseline)": ma_crossover,
    }

    print("=" * 60)
    print("  ABLATION STUDY")
    print("=" * 60)

    for name, signal_fn in variants.items():
        result = run_vectorized_backtest(candles, signal_fn, config)
        print_report(result, name)
        print()


if __name__ == "__main__":
    # Generate synthetic data for demonstration
    np.random.seed(42)
    n = 2000
    prices = 50000 * np.cumprod(1 + np.random.normal(0.0002, 0.015, n))
    times = pd.date_range("2023-01-01", periods=n, freq="4h", tz="UTC")

    candles = pd.DataFrame(
        {
            "time": times,
            "open": prices * (1 - np.random.uniform(0, 0.003, n)),
            "high": prices * (1 + np.random.uniform(0, 0.008, n)),
            "low": prices * (1 - np.random.uniform(0, 0.008, n)),
            "close": prices,
            "volume": np.random.uniform(50, 500, n),
        }
    )

    run_ablation(candles)
