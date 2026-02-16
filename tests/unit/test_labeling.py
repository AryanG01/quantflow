"""Tests for triple-barrier labeling."""

from __future__ import annotations

import numpy as np
import pandas as pd

from packages.models.labeling import triple_barrier_labels


class TestTripleBarrierLabeling:
    def test_strong_uptrend_labels_up(self) -> None:
        """Strong uptrend should produce label 2 (up)."""
        # Price rises 5% over 5 bars → should hit 3% profit target
        prices = pd.Series([100.0, 101.0, 102.0, 103.5, 105.0, 106.0])
        labels = triple_barrier_labels(
            prices, profit_taking_pct=0.03, stop_loss_pct=0.015, max_holding_bars=5
        )
        assert labels[0] == 2  # first bar should be labeled up

    def test_strong_downtrend_labels_down(self) -> None:
        """Strong downtrend should produce label 0 (down)."""
        # Price drops 2% quickly → should hit 1.5% stop loss
        prices = pd.Series([100.0, 99.0, 98.0, 97.0, 96.0, 95.0])
        labels = triple_barrier_labels(
            prices, profit_taking_pct=0.03, stop_loss_pct=0.015, max_holding_bars=5
        )
        assert labels[0] == 0  # first bar labeled down

    def test_flat_market_labels_neutral(self) -> None:
        """Flat market should produce label 1 (neutral)."""
        prices = pd.Series([100.0, 100.1, 99.9, 100.05, 100.02, 99.98])
        labels = triple_barrier_labels(
            prices, profit_taking_pct=0.03, stop_loss_pct=0.015, max_holding_bars=5
        )
        assert labels[0] == 1

    def test_last_bar_unlabeled(self) -> None:
        """Last bar can't be labeled (no future data)."""
        prices = pd.Series([100.0, 101.0, 102.0])
        labels = triple_barrier_labels(prices, max_holding_bars=5)
        assert labels[-1] == -1  # unlabeled

    def test_label_values_valid(self) -> None:
        """All labels should be in {-1, 0, 1, 2}."""
        np.random.seed(42)
        prices = pd.Series(100 * np.cumprod(1 + np.random.normal(0, 0.02, 200)))
        labels = triple_barrier_labels(prices)
        assert set(np.unique(labels)).issubset({-1, 0, 1, 2})

    def test_profit_taking_triggers_before_stop(self) -> None:
        """If profit target is hit before stop, label should be up."""
        # Price goes up first, then down
        prices = pd.Series([100.0, 103.5, 97.0, 95.0, 93.0])
        labels = triple_barrier_labels(
            prices, profit_taking_pct=0.03, stop_loss_pct=0.05, max_holding_bars=10
        )
        assert labels[0] == 2  # profit hit first
