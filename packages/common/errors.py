"""Exception hierarchy for the AI Trading System."""

from __future__ import annotations


class TradingError(Exception):
    """Base exception for all trading system errors."""


class DataError(TradingError):
    """Errors related to data ingestion or processing."""


class ExchangeError(TradingError):
    """Errors related to exchange API interactions."""


class RateLimitError(ExchangeError):
    """Exchange rate limit exceeded."""


class ModelError(TradingError):
    """Errors related to ML model training or prediction."""


class RiskError(TradingError):
    """Errors related to risk management."""


class KillSwitchError(RiskError):
    """Kill switch triggered — halt all trading."""


class ConfigError(TradingError):
    """Errors related to configuration loading or validation."""
