"""Integration test for Binance adapter — fetches real candles."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from packages.common.config import ExchangeConfig
from packages.data_ingestion.binance_adapter import BinanceAdapter


@pytest.mark.integration
class TestBinanceAdapter:
    def test_fetch_10_candles(self) -> None:
        """Fetch 10 candles from Binance and verify schema."""
        config = ExchangeConfig(sandbox=False, rate_limit_rpm=1200)
        adapter = BinanceAdapter(config)

        since = datetime.now(timezone.utc) - timedelta(days=3)

        async def run() -> None:
            try:
                candles = await adapter.fetch_candles(
                    symbol="BTC/USDT",
                    timeframe="4h",
                    since=since,
                    limit=10,
                )

                assert len(candles) > 0
                assert len(candles) <= 10

                for c in candles:
                    assert c.exchange == "binance"
                    assert c.symbol == "BTC/USDT"
                    assert c.timeframe == "4h"
                    assert c.open > 0
                    assert c.high >= c.low
                    assert c.close > 0
                    assert c.volume >= 0
                    assert c.time.tzinfo is not None  # UTC-aware
            finally:
                await adapter.close()

        asyncio.run(run())
