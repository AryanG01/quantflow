"""Backtest performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

ANNUALIZATION_FACTOR_4H = np.sqrt(6 * 365)  # 6 bars/day * 365 days


@dataclass
class BacktestMetrics:
    """Summary metrics for a backtest run."""

    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration_bars: int
    hit_rate: float
    profit_factor: float
    total_trades: int
    turnover_annual: float
    calmar_ratio: float


def compute_sharpe(returns: npt.NDArray[np.float64], annualize: float = 0.0) -> float:
    """Compute Sharpe ratio. Uses 4h annualization by default."""
    if annualize == 0.0:
        annualize = float(ANNUALIZATION_FACTOR_4H)
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    return float(np.mean(returns) / np.std(returns) * annualize)


def compute_sortino(returns: npt.NDArray[np.float64], annualize: float = 0.0) -> float:
    """Compute Sortino ratio (downside deviation only)."""
    if annualize == 0.0:
        annualize = float(ANNUALIZATION_FACTOR_4H)
    downside = returns[returns < 0]
    if len(downside) == 0 or np.std(downside) == 0:
        return 0.0
    return float(np.mean(returns) / np.std(downside) * annualize)


def compute_max_drawdown(equity_curve: npt.NDArray[np.float64]) -> tuple[float, int]:
    """Compute max drawdown percentage and duration in bars.

    Returns:
        (max_drawdown_pct, max_drawdown_duration_bars)
    """
    if len(equity_curve) == 0:
        return 0.0, 0

    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / np.maximum(peak, 1e-10)
    max_dd = float(np.min(drawdown))

    # Duration: longest streak below peak
    below_peak = equity_curve < peak
    if not np.any(below_peak):
        return abs(max_dd), 0

    max_duration = 0
    current_duration = 0
    for b in below_peak:
        if b:
            current_duration += 1
            max_duration = max(max_duration, current_duration)
        else:
            current_duration = 0

    return abs(max_dd), max_duration


def compute_hit_rate(trade_returns: npt.NDArray[np.float64]) -> float:
    """Fraction of trades that were profitable."""
    if len(trade_returns) == 0:
        return 0.0
    return float(np.mean(trade_returns > 0))


def compute_profit_factor(trade_returns: npt.NDArray[np.float64]) -> float:
    """Gross profit / gross loss."""
    gains = trade_returns[trade_returns > 0].sum()
    losses = abs(trade_returns[trade_returns < 0].sum())
    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return float(gains / losses)


def compute_all_metrics(
    equity_curve: npt.NDArray[np.float64],
    returns: npt.NDArray[np.float64],
    trade_returns: npt.NDArray[np.float64],
    total_trades: int,
    n_bars: int,
) -> BacktestMetrics:
    """Compute all backtest metrics."""
    total_return = float(equity_curve[-1] / equity_curve[0] - 1) if len(equity_curve) > 0 else 0.0

    bars_per_year = 6 * 365  # 4h bars
    n_years = n_bars / bars_per_year if bars_per_year > 0 else 1.0
    annualized_return = (1 + total_return) ** (1 / n_years) - 1 if n_years > 0 else 0.0

    sharpe = compute_sharpe(returns)
    sortino = compute_sortino(returns)
    max_dd, max_dd_duration = compute_max_drawdown(equity_curve)
    hit_rate = compute_hit_rate(trade_returns)
    profit_factor = compute_profit_factor(trade_returns)

    # Turnover: sum of absolute position changes / n_years
    turnover = float(np.sum(np.abs(np.diff(returns)))) / n_years if n_years > 0 else 0.0

    calmar = annualized_return / max_dd if max_dd > 0 else 0.0

    return BacktestMetrics(
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe,
        sortino_ratio=sortino,
        max_drawdown=max_dd,
        max_drawdown_duration_bars=max_dd_duration,
        hit_rate=hit_rate,
        profit_factor=profit_factor,
        total_trades=total_trades,
        turnover_annual=turnover,
        calmar_ratio=calmar,
    )
