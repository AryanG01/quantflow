"""Orderbook-based features (placeholder for live data)."""

from __future__ import annotations

import pandas as pd

from packages.features.interfaces import FeatureComputer


class OrderbookFeatures(FeatureComputer):
    """Orderbook imbalance features.

    These features require live orderbook snapshots. For backtesting
    without orderbook data, this returns NaN columns that should be
    dropped or filled before model training.
    """

    def compute(self, candles: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame(index=candles.index)
        features["bid_ask_imbalance"] = float("nan")
        features["depth_ratio_5"] = float("nan")
        return features

    def feature_names(self) -> list[str]:
        return ["bid_ask_imbalance", "depth_ratio_5"]
