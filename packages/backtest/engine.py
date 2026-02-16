"""Event-driven backtest engine (v2).

Processes events in sequence: BAR_CLOSE → SIGNAL → ORDER → FILL.
Supports partial fills, latency simulation, and realistic cost modeling.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import numpy.typing as npt
import pandas as pd

from packages.backtest.cost_model import CostModel, CostModelConfig
from packages.backtest.metrics import BacktestMetrics, compute_all_metrics


class EventType(Enum):
    BAR_CLOSE = "bar_close"
    SIGNAL = "signal"
    ORDER = "order"
    FILL = "fill"


@dataclass
class Event:
    type: EventType
    bar_idx: int
    data: dict[str, float] = field(default_factory=dict)


@dataclass
class EventDrivenConfig:
    initial_capital: float = 100_000.0
    cost_model: CostModelConfig | None = None
    adv_window: int = 20
    fill_delay_bars: int = 0  # 0 = fill on same bar
    partial_fill_pct: float = 1.0  # 1.0 = always full fill


@dataclass
class EventDrivenResult:
    equity_curve: npt.NDArray[np.float64]
    returns: npt.NDArray[np.float64]
    positions: npt.NDArray[np.float64]
    trade_returns: npt.NDArray[np.float64]
    metrics: BacktestMetrics
    timestamps: npt.NDArray[np.datetime64]
    events: list[Event]


SignalFn = Callable[[pd.DataFrame], npt.NDArray[np.float64]]


def run_event_driven_backtest(
    candles: pd.DataFrame,
    signal_fn: SignalFn,
    config: EventDrivenConfig | None = None,
) -> EventDrivenResult:
    """Run an event-driven backtest with realistic fill simulation."""
    config = config or EventDrivenConfig()
    cost_model = CostModel(config.cost_model)

    df = candles.sort_values("time").reset_index(drop=True)
    closes = df["close"].values.astype(np.float64)
    volumes = df["volume"].values.astype(np.float64)
    n = len(closes)

    # Pre-compute signals
    target_positions = signal_fn(df)

    # State tracking
    equity = np.zeros(n)
    actual_positions = np.zeros(n)
    cash = config.initial_capital
    position_qty = 0.0  # in units (fractional shares)
    events: list[Event] = []
    trade_returns_list: list[float] = []

    # ADV for cost model
    dollar_volume = closes * volumes
    adv = pd.Series(dollar_volume).rolling(config.adv_window, min_periods=1).mean().values

    pending_orders: list[tuple[int, float]] = []  # (fill_bar, target_position)

    for i in range(n):
        price = closes[i]

        # Process fills for this bar
        new_pending = []
        for fill_bar, target_pos in pending_orders:
            if i >= fill_bar:
                # Execute fill
                pos_change = target_pos - actual_positions[max(0, i - 1)]
                if abs(pos_change) > 1e-10:
                    fill_pct = config.partial_fill_pct
                    actual_change = pos_change * fill_pct

                    trade_value = abs(actual_change) * config.initial_capital
                    cost_pct = cost_model.compute_costs_pct(
                        np.array([trade_value]), np.array([adv[i]])
                    )[0]
                    cost_dollar = cost_pct * trade_value

                    cash -= actual_change * config.initial_capital
                    cash -= cost_dollar
                    position_qty += actual_change

                    events.append(
                        Event(
                            type=EventType.FILL,
                            bar_idx=i,
                            data={
                                "position_change": actual_change,
                                "cost": cost_dollar,
                                "price": price,
                            },
                        )
                    )

                    if abs(pos_change) > 0.01:
                        trade_returns_list.append(-cost_pct)
            else:
                new_pending.append((fill_bar, target_pos))
        pending_orders = new_pending

        # Record bar close event
        events.append(Event(type=EventType.BAR_CLOSE, bar_idx=i, data={"price": price}))

        # Generate signal event
        target_pos = float(target_positions[i])
        current_pos = position_qty
        events.append(
            Event(
                type=EventType.SIGNAL,
                bar_idx=i,
                data={"target": target_pos, "current": current_pos},
            )
        )

        # Generate order if position change needed
        if abs(target_pos - current_pos) > 1e-10:
            fill_bar = i + config.fill_delay_bars
            pending_orders.append((fill_bar, target_pos))
            events.append(Event(type=EventType.ORDER, bar_idx=i, data={"target": target_pos}))

        actual_positions[i] = position_qty

        # Mark-to-market
        position_value = (
            position_qty * config.initial_capital * (price / closes[0] if closes[0] > 0 else 1)
        )
        equity[i] = cash + position_value

    # Compute returns
    returns = np.zeros(n)
    returns[1:] = equity[1:] / equity[:-1] - 1

    trade_returns = np.array(trade_returns_list) if trade_returns_list else np.array([])

    trade_indices = np.where(np.abs(np.diff(actual_positions)) > 1e-10)[0]

    metrics = compute_all_metrics(
        equity_curve=equity,
        returns=returns,
        trade_returns=trade_returns,
        total_trades=len(trade_indices),
        n_bars=n,
    )

    return EventDrivenResult(
        equity_curve=equity,
        returns=returns,
        positions=actual_positions,
        trade_returns=trade_returns,
        metrics=metrics,
        timestamps=df["time"].values,
        events=events,
    )
