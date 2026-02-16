"""Abstract interfaces for market data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from packages.common.types import Candle


class MarketDataProvider(ABC):
    """Abstract base class for exchange data adapters."""

    @abstractmethod
    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        limit: int = 500,
    ) -> list[Candle]:
        """Fetch OHLCV candle data from the exchange.

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Bar size (e.g., "4h")
            since: Start time (UTC)
            limit: Max candles to fetch per request

        Returns:
            List of Candle objects sorted by time ascending
        """

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> dict[str, float]:
        """Fetch current ticker (bid, ask, last, volume)."""

    @abstractmethod
    async def fetch_orderbook(
        self, symbol: str, limit: int = 20
    ) -> dict[str, list[list[float]]]:
        """Fetch orderbook snapshot (bids, asks as [[price, qty], ...])."""

    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the exchange identifier."""
