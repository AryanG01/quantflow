"""Abstract interfaces for feature computation."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class FeatureComputer(ABC):
    """Base class for feature computation modules."""

    @abstractmethod
    def compute(self, candles: pd.DataFrame) -> pd.DataFrame:
        """Compute features from candle data.

        Args:
            candles: DataFrame with columns [time, open, high, low, close, volume]

        Returns:
            DataFrame with feature columns, indexed aligned with input.
            All features must use only past data (no lookahead).
        """

    @abstractmethod
    def feature_names(self) -> list[str]:
        """Return list of feature column names produced by this computer."""
