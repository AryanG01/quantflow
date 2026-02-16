"""Triple-barrier labeling for ML targets.

Labels each bar based on which barrier is hit first:
- Upper barrier (profit taking) → label 2 (up)
- Lower barrier (stop loss) → label 0 (down)
- Time barrier (max holding period) → label based on final return
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd


def triple_barrier_labels(
    close: pd.Series,  # type: ignore[type-arg]
    profit_taking_pct: float = 0.03,
    stop_loss_pct: float = 0.015,
    max_holding_bars: int = 12,
) -> npt.NDArray[np.int64]:
    """Apply triple-barrier labeling to a price series.

    Args:
        close: Close price series
        profit_taking_pct: Upper barrier as fraction (e.g., 0.03 = 3%)
        stop_loss_pct: Lower barrier as fraction (e.g., 0.015 = 1.5%)
        max_holding_bars: Maximum bars before time barrier

    Returns:
        Array of labels: 0=down, 1=neutral, 2=up
        NaN-equivalent (-1) for bars where labeling is impossible (end of series)
    """
    n = len(close)
    prices = close.values.astype(np.float64)
    labels = np.full(n, -1, dtype=np.int64)

    for i in range(n):
        entry_price = prices[i]
        upper = entry_price * (1 + profit_taking_pct)
        lower = entry_price * (1 - stop_loss_pct)

        end_idx = min(i + max_holding_bars, n - 1)

        if i >= n - 1:
            continue

        label_assigned = False
        for j in range(i + 1, end_idx + 1):
            if prices[j] >= upper:
                labels[i] = 2  # up — hit profit target
                label_assigned = True
                break
            elif prices[j] <= lower:
                labels[i] = 0  # down — hit stop loss
                label_assigned = True
                break

        if not label_assigned:
            # Time barrier hit: label based on return
            final_return = prices[end_idx] / entry_price - 1
            if final_return > 0.005:  # small positive threshold
                labels[i] = 2
            elif final_return < -0.005:
                labels[i] = 0
            else:
                labels[i] = 1  # neutral

    return labels
