"""CLI script to run backtest with configuration."""

from __future__ import annotations

import numpy as np
import pandas as pd

from packages.backtest.benchmarks import buy_and_hold, ma_crossover, mean_reversion
from packages.backtest.engine_vectorized import BacktestConfig, run_vectorized_backtest
from packages.backtest.monte_carlo import bootstrap_returns
from packages.backtest.report import print_report
from packages.common.config import load_config


def main() -> None:
    cfg = load_config()

    # Generate synthetic data for now (replaced by DB fetch in production)
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

    config = BacktestConfig(initial_capital=100_000.0)

    strategies = {
        "Buy & Hold": buy_and_hold,
        "MA Crossover (20/50)": ma_crossover,
        "Mean Reversion": mean_reversion,
    }

    for name, signal_fn in strategies.items():
        result = run_vectorized_backtest(candles, signal_fn, config)
        print_report(result, name)

        # Monte Carlo
        mc = bootstrap_returns(result.returns, n_simulations=500)
        print(f"  Monte Carlo (500 sims):")
        print(f"    Sharpe 5th pct: {mc.sharpe_5th_percentile:.2f}")
        print(f"    Sharpe mean:    {mc.sharpe_mean:.2f}")
        print(f"    Sharpe 95th pct: {mc.sharpe_95th_percentile:.2f}")
        print()


if __name__ == "__main__":
    main()
