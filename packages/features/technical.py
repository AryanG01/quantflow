"""Technical indicator features.

All indicators use .shift(1) where needed to prevent lookahead.
Features are computed from OHLCV candle data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from packages.features.interfaces import FeatureComputer


class TechnicalFeatures(FeatureComputer):
    """Compute standard technical indicators from OHLCV data."""

    def __init__(
        self,
        rsi_period: int = 14,
        atr_period: int = 14,
        bb_period: int = 20,
        bb_std: float = 2.0,
        vol_window: int = 24,
        vwap_period: int = 24,
    ) -> None:
        self._rsi_period = rsi_period
        self._atr_period = atr_period
        self._bb_period = bb_period
        self._bb_std = bb_std
        self._vol_window = vol_window
        self._vwap_period = vwap_period

    def compute(self, candles: pd.DataFrame) -> pd.DataFrame:
        close = candles["close"]
        high = candles["high"]
        low = candles["low"]
        volume = candles["volume"]

        features = pd.DataFrame(index=candles.index)

        # Log returns
        features["log_returns"] = np.log(close / close.shift(1))

        # RSI
        features["rsi"] = self._compute_rsi(close, self._rsi_period)

        # ATR (Average True Range)
        features["atr"] = self._compute_atr(high, low, close, self._atr_period)

        # Bollinger %B
        features["bb_pct_b"] = self._compute_bollinger_pct_b(
            close, self._bb_period, self._bb_std
        )

        # VWAP deviation
        features["vwap_deviation"] = self._compute_vwap_deviation(
            close, volume, self._vwap_period
        )

        # Realized volatility (annualized from bar returns)
        log_ret = features["log_returns"]
        features["realized_vol"] = log_ret.rolling(self._vol_window).std() * np.sqrt(
            6 * 365
        )  # 4h bars

        return features

    def feature_names(self) -> list[str]:
        return [
            "log_returns",
            "rsi",
            "atr",
            "bb_pct_b",
            "vwap_deviation",
            "realized_vol",
        ]

    @staticmethod
    def _compute_rsi(close: pd.Series, period: int) -> pd.Series:  # type: ignore[type-arg]
        """RSI using exponential moving average of gains/losses."""
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.ewm(span=period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(span=period, min_periods=period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def _compute_atr(
        high: pd.Series,  # type: ignore[type-arg]
        low: pd.Series,  # type: ignore[type-arg]
        close: pd.Series,  # type: ignore[type-arg]
        period: int,
    ) -> pd.Series:  # type: ignore[type-arg]
        """Average True Range."""
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(period).mean()

    @staticmethod
    def _compute_bollinger_pct_b(
        close: pd.Series,  # type: ignore[type-arg]
        period: int,
        std_dev: float,
    ) -> pd.Series:  # type: ignore[type-arg]
        """Bollinger %B: (close - lower) / (upper - lower)."""
        sma = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = sma + std_dev * std
        lower = sma - std_dev * std
        band_width = upper - lower
        pct_b = (close - lower) / band_width.replace(0, np.nan)
        return pct_b

    @staticmethod
    def _compute_vwap_deviation(
        close: pd.Series,  # type: ignore[type-arg]
        volume: pd.Series,  # type: ignore[type-arg]
        period: int,
    ) -> pd.Series:  # type: ignore[type-arg]
        """Deviation of close from rolling VWAP."""
        cum_vol = volume.rolling(period).sum()
        cum_pv = (close * volume).rolling(period).sum()
        vwap = cum_pv / cum_vol.replace(0, np.nan)
        return (close - vwap) / vwap.replace(0, np.nan)
