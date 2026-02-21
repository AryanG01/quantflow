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
        bars_per_year: int = 2190,
    ) -> None:
        self._rsi_period = rsi_period
        self._atr_period = atr_period
        self._bb_period = bb_period
        self._bb_std = bb_std
        self._vol_window = vol_window
        self._vwap_period = vwap_period
        self._bars_per_year = bars_per_year

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
        features["bb_pct_b"] = self._compute_bollinger_pct_b(close, self._bb_period, self._bb_std)

        # VWAP deviation
        features["vwap_deviation"] = self._compute_vwap_deviation(close, volume, self._vwap_period)

        # Realized volatility (annualized from bar returns)
        log_ret = features["log_returns"]
        features["realized_vol"] = log_ret.rolling(self._vol_window).std() * np.sqrt(
            self._bars_per_year
        )

        # Momentum features (shifted 1 bar to prevent lookahead)
        features["momentum_4"] = (close / close.shift(4) - 1).shift(1)
        features["momentum_12"] = (close / close.shift(12) - 1).shift(1)

        # EMA ratio: short-term vs long-term trend strength (shifted 1 bar)
        ema_fast = close.ewm(span=10, adjust=False).mean()
        ema_slow = close.ewm(span=30, adjust=False).mean()
        features["ema_ratio"] = (ema_fast / ema_slow.replace(0, np.nan) - 1).shift(1)

        # Volume anomaly: current volume vs rolling mean (shifted 1 bar)
        features["volume_ratio"] = (
            volume / volume.rolling(24).mean().replace(0, np.nan) - 1
        ).shift(1)

        return features

    def feature_names(self) -> list[str]:
        return [
            "log_returns",
            "rsi",
            "atr",
            "bb_pct_b",
            "vwap_deviation",
            "realized_vol",
            "momentum_4",
            "momentum_12",
            "ema_ratio",
            "volume_ratio",
        ]

    @staticmethod
    def _compute_rsi(close: pd.Series, period: int) -> pd.Series:
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
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int,
    ) -> pd.Series:
        """Average True Range."""
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range.rolling(period).mean()

    @staticmethod
    def _compute_bollinger_pct_b(
        close: pd.Series,
        period: int,
        std_dev: float,
    ) -> pd.Series:
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
        close: pd.Series,
        volume: pd.Series,
        period: int,
    ) -> pd.Series:
        """Deviation of close from rolling VWAP."""
        cum_vol = volume.rolling(period).sum()
        cum_pv = (close * volume).rolling(period).sum()
        vwap = cum_pv / cum_vol.replace(0, np.nan)
        return (close - vwap) / vwap.replace(0, np.nan)
