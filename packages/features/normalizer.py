"""Feature normalization with lookahead prevention."""

from __future__ import annotations

import pandas as pd


class RollingZScoreNormalizer:
    """Rolling z-score normalization using only past data.

    Uses .shift(1) on rolling stats to ensure the current bar's value
    is not used in computing its own z-score — preventing lookahead bias.
    """

    def __init__(self, window: int = 100, shift: int = 1) -> None:
        self._window = window
        self._shift = shift

    def normalize(self, features: pd.DataFrame) -> pd.DataFrame:
        """Normalize each feature column to a rolling z-score.

        Args:
            features: DataFrame with numeric feature columns

        Returns:
            DataFrame with z-scored features (same shape)
        """
        rolling_mean = features.rolling(self._window, min_periods=self._window).mean()
        rolling_std = features.rolling(self._window, min_periods=self._window).std()

        # Shift stats to prevent lookahead
        shifted_mean = rolling_mean.shift(self._shift)
        shifted_std = rolling_std.shift(self._shift).clip(lower=1e-10)

        normalized = (features - shifted_mean) / shifted_std
        return normalized
