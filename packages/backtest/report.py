"""Backtest report generation."""

from __future__ import annotations

from typing import Any


def format_report(result: Any, strategy_name: str = "Strategy") -> str:
    """Format backtest metrics as a readable report."""
    m = result.metrics
    lines = [
        f"{'=' * 50}",
        f"  Backtest Report: {strategy_name}",
        f"{'=' * 50}",
        f"  Total Return:          {m.total_return:>10.2%}",
        f"  Annualized Return:     {m.annualized_return:>10.2%}",
        f"  Sharpe Ratio:          {m.sharpe_ratio:>10.2f}",
        f"  Sortino Ratio:         {m.sortino_ratio:>10.2f}",
        f"  Calmar Ratio:          {m.calmar_ratio:>10.2f}",
        f"  Max Drawdown:          {m.max_drawdown:>10.2%}",
        f"  Max DD Duration:       {m.max_drawdown_duration_bars:>10d} bars",
        f"  Hit Rate:              {m.hit_rate:>10.2%}",
        f"  Profit Factor:         {m.profit_factor:>10.2f}",
        f"  Total Trades:          {m.total_trades:>10d}",
        f"  Annual Turnover:       {m.turnover_annual:>10.2f}",
        f"{'=' * 50}",
    ]
    return "\n".join(lines)


def print_report(result: Any, strategy_name: str = "Strategy") -> None:
    """Print backtest report to stdout."""
    print(format_report(result, strategy_name))
