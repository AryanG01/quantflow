"""Coinbase market data adapter using ccxt."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import ccxt.async_support as ccxt

from packages.common.errors import ExchangeError
from packages.common.logging import get_logger
from packages.common.types import Candle
from packages.data_ingestion.interfaces import MarketDataProvider
from packages.data_ingestion.rate_limiter import TokenBucketRateLimiter

if TYPE_CHECKING:
    from packages.common.config import ExchangeConfig

logger = get_logger(__name__)


class CoinbaseAdapter(MarketDataProvider):
    """Coinbase exchange adapter via ccxt."""

    def __init__(
        self,
        config: ExchangeConfig,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = "",
    ) -> None:
        self._exchange = ccxt.coinbase(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "password": passphrase,
                "sandbox": config.sandbox,
                "enableRateLimit": False,
            }
        )
        self._rate_limiter = TokenBucketRateLimiter(config.rate_limit_rpm)

    async def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        since: datetime,
        limit: int = 300,
    ) -> list[Candle]:
        await self._rate_limiter.acquire()
        since_ms = int(since.timestamp() * 1000)

        try:
            ohlcv = await self._exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=limit)
        except ccxt.BaseError as e:
            raise ExchangeError(f"Coinbase fetch_candles failed: {e}") from e

        candles = []
        for row in ohlcv:
            ts_ms, o, h, lo, c, v = row[0], row[1], row[2], row[3], row[4], row[5]
            candles.append(
                Candle(
                    time=datetime.fromtimestamp(ts_ms / 1000, tz=UTC),
                    exchange="coinbase",
                    symbol=symbol,
                    timeframe=timeframe,
                    open=float(o),
                    high=float(h),
                    low=float(lo),
                    close=float(c),
                    volume=float(v),
                )
            )

        logger.debug(
            "fetched_candles",
            exchange="coinbase",
            symbol=symbol,
            count=len(candles),
        )
        return candles

    async def fetch_ticker(self, symbol: str) -> dict[str, float]:
        await self._rate_limiter.acquire()
        try:
            ticker = await self._exchange.fetch_ticker(symbol)
        except ccxt.BaseError as e:
            raise ExchangeError(f"Coinbase fetch_ticker failed: {e}") from e
        return {
            "bid": float(ticker.get("bid", 0)),
            "ask": float(ticker.get("ask", 0)),
            "last": float(ticker.get("last", 0)),
            "volume": float(ticker.get("baseVolume", 0)),
        }

    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> dict[str, list[list[float]]]:
        await self._rate_limiter.acquire()
        try:
            book = await self._exchange.fetch_order_book(symbol, limit)
        except ccxt.BaseError as e:
            raise ExchangeError(f"Coinbase fetch_orderbook failed: {e}") from e
        return {"bids": book["bids"], "asks": book["asks"]}

    def get_exchange_name(self) -> str:
        return "coinbase"

    async def close(self) -> None:
        await self._exchange.close()
