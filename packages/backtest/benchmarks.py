"""Benchmark signal functions for backtesting."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd


def buy_and_hold(candles: pd.DataFrame) -> npt.NDArray[np.float64]:
    """Always long. The simplest benchmark."""
    return np.ones(len(candles))


def ma_crossover(
    candles: pd.DataFrame,
    fast_period: int = 20,
    slow_period: int = 50,
) -> npt.NDArray[np.float64]:
    """Moving average crossover: long when fast MA > slow MA, else flat.

    Uses .shift(1) on MAs to prevent lookahead — signal is based on
    prior bar's moving averages, executed at current bar's close.
    """
    closes = candles["close"]

    fast_ma = closes.rolling(fast_period, min_periods=fast_period).mean().shift(1)
    slow_ma = closes.rolling(slow_period, min_periods=slow_period).mean().shift(1)

    positions = np.where(fast_ma > slow_ma, 1.0, 0.0)
    # Zero out warmup period
    positions[: slow_period + 1] = 0.0

    return positions


def mean_reversion(
    candles: pd.DataFrame,
    lookback: int = 20,
    entry_zscore: float = -1.5,
    exit_zscore: float = 0.0,
) -> npt.NDArray[np.float64]:
    """Mean reversion: buy when z-score drops below threshold, exit at mean.

    Uses .shift(1) on rolling stats to prevent lookahead.
    """
    closes = candles["close"]

    rolling_mean = closes.rolling(lookback, min_periods=lookback).mean().shift(1)
    rolling_std = closes.rolling(lookback, min_periods=lookback).std().shift(1)

    zscore = (closes - rolling_mean) / rolling_std.clip(lower=1e-10)

    n = len(closes)
    positions = np.zeros(n)

    in_position = False
    for i in range(lookback + 1, n):
        z = zscore.iloc[i]
        if not in_position and z < entry_zscore:
            in_position = True
            positions[i] = 1.0
        elif in_position and z > exit_zscore:
            in_position = False
            positions[i] = 0.0
        elif in_position:
            positions[i] = 1.0

    return positions
