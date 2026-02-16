"""Vectorized backtest engine (v1).

Takes candle data and a signal function, applies a cost model,
and produces an equity curve with performance metrics.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import pandas as pd

from packages.backtest.cost_model import CostModel, CostModelConfig
from packages.backtest.metrics import BacktestMetrics, compute_all_metrics


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    initial_capital: float = 100_000.0
    cost_model: CostModelConfig | None = None
    adv_window: int = 20  # bars for average daily volume


@dataclass
class BacktestResult:
    """Result of a backtest run."""

    equity_curve: npt.NDArray[np.float64]
    returns: npt.NDArray[np.float64]
    positions: npt.NDArray[np.float64]
    trade_returns: npt.NDArray[np.float64]
    metrics: BacktestMetrics
    timestamps: npt.NDArray[np.datetime64]


# Signal function: takes OHLCV DataFrame, returns position array [-1, 0, 1]
SignalFn = Callable[..., npt.NDArray[np.float64]]


def run_vectorized_backtest(
    candles: pd.DataFrame,
    signal_fn: SignalFn,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Run a vectorized backtest.

    Args:
        candles: DataFrame with columns [time, open, high, low, close, volume]
        signal_fn: Function that takes candles and returns position array.
                   Values in [-1, 1] where -1=full short, 0=flat, 1=full long.
                   MUST use only past data (no lookahead).
        config: Backtest configuration

    Returns:
        BacktestResult with equity curve, metrics, etc.
    """
    config = config or BacktestConfig()
    cost_model = CostModel(config.cost_model)

    df = candles.sort_values("time").reset_index(drop=True)
    closes = df["close"].values.astype(np.float64)
    volumes = df["volume"].values.astype(np.float64)
    n = len(closes)

    # Generate signals (position sizing from -1 to 1)
    positions = signal_fn(df)
    assert len(positions) == n, f"Signal length {len(positions)} != candle length {n}"

    # Compute bar returns
    bar_returns = np.zeros(n)
    bar_returns[1:] = closes[1:] / closes[:-1] - 1

    # Compute position changes (trades)
    position_changes = np.zeros(n)
    position_changes[1:] = np.abs(positions[1:] - positions[:-1])

    # Average daily volume (in dollar terms) for cost model
    dollar_volume = closes * volumes
    adv = pd.Series(dollar_volume).rolling(config.adv_window, min_periods=1).mean().values

    # Trade values (dollar value of position change)
    trade_values = position_changes * config.initial_capital

    # Transaction costs
    costs_pct = cost_model.compute_costs_pct(
        trade_values.astype(np.float64),
        adv.astype(np.float64),
    )

    # Strategy returns: position * bar_return - costs on trade bars
    strategy_returns = positions * bar_returns - costs_pct * position_changes

    # Equity curve
    equity_curve = np.asarray(
        config.initial_capital * np.cumprod(1 + strategy_returns), dtype=np.float64
    )

    # Extract per-trade returns (each position change starts a new trade)
    trade_indices = np.where(position_changes > 0)[0]
    trade_returns_list: list[float] = []
    for i in range(len(trade_indices) - 1):
        start_idx = trade_indices[i]
        end_idx = trade_indices[i + 1]
        trade_ret = float(np.prod(1 + strategy_returns[start_idx:end_idx]) - 1)
        trade_returns_list.append(trade_ret)
    trade_returns = np.array(trade_returns_list) if trade_returns_list else np.array([])

    timestamps = df["time"].values

    metrics = compute_all_metrics(
        equity_curve=equity_curve,
        returns=strategy_returns,
        trade_returns=trade_returns,
        total_trades=len(trade_indices),
        n_bars=n,
    )

    return BacktestResult(
        equity_curve=equity_curve,
        returns=strategy_returns,
        positions=positions,
        trade_returns=trade_returns,
        metrics=metrics,
        timestamps=timestamps,
    )
