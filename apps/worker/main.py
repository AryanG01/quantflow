"""Worker process: scheduled tasks for the trading system.

Scheduling:
- Every 4h: signal pipeline (features → predict → regime → fuse → risk → execute)
- Every 1h: candle ingestion (backfill recent candles from exchange)
- Every 5m: sentiment cleanup, orderbook snapshots, order status polling
- Every 1m: health check, drawdown monitoring, risk metrics persistence
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import sqlalchemy as sa

from apps.worker.tasks.signal_pipeline import SignalPipeline
from packages.common.config import AppConfig, load_config
from packages.common.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _create_engine(config: AppConfig) -> sa.engine.Engine:
    """Create a SQLAlchemy engine from database config."""
    return sa.create_engine(config.database.url, pool_pre_ping=True, pool_size=5)


class Worker:
    """Manages scheduled tasks and shared resources."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._engine = _create_engine(config)
        self._pipeline = SignalPipeline(config, self._engine)

    async def signal_pipeline_task(self) -> None:
        """Main signal generation pipeline — runs every 4h."""
        logger.info("signal_pipeline_started", time=datetime.now(UTC).isoformat())
        try:
            await self._pipeline.run()
            logger.info("signal_pipeline_completed")
        except Exception as e:
            logger.error("signal_pipeline_failed", error=str(e))

    async def candle_ingestion_task(self) -> None:
        """Backfill recent candles from exchange — runs every 1h."""
        try:
            from packages.common.config import ExchangeConfig
            from packages.data_ingestion.backfill import backfill_candles
            from packages.data_ingestion.binance_adapter import BinanceAdapter

            exchange_cfg = self._config.exchanges.get("binance", ExchangeConfig())
            adapter = BinanceAdapter(config=exchange_cfg)
            start = datetime.now(UTC) - timedelta(hours=2)

            for symbol in self._config.universe.symbols:
                inserted = await backfill_candles(
                    provider=adapter,
                    engine=self._engine,
                    symbol=symbol,
                    timeframe=self._config.universe.timeframe,
                    start=start,
                )
                if inserted > 0:
                    logger.info("candles_ingested", symbol=symbol, count=inserted)
        except Exception as e:
            logger.warning("candle_ingestion_failed", error=str(e))

    async def sentiment_task(self) -> None:
        """Sentiment cleanup — runs every 5 minutes.

        Clears stale events from the in-memory scorer.
        Full ingestion (CryptoPanic/Reddit) requires API keys and is a separate concern.
        """
        try:
            cutoff = datetime.now(UTC) - timedelta(hours=24)
            removed = self._pipeline._sentiment_scorer.clear_old_events(cutoff)
            if removed > 0:
                logger.debug("sentiment_stale_events_cleared", count=removed)
        except Exception as e:
            logger.warning("sentiment_task_failed", error=str(e))

    async def health_check_task(self) -> None:
        """Health and drawdown monitoring — runs every 1 minute.

        Persists current risk metrics so the API dashboard stays fresh
        between 4h pipeline runs.
        """
        try:
            self._pipeline._persist_risk_metrics()
        except Exception as e:
            logger.warning("health_check_failed", error=str(e))

    async def run(self) -> None:
        """Main worker loop with scheduled tasks."""
        logger.info("worker_started", mode=self._config.execution.mode)

        signal_interval = 4 * 60 * 60  # 4 hours
        candle_interval = 60 * 60  # 1 hour
        sentiment_interval = 5 * 60  # 5 minutes
        health_interval = 60  # 1 minute

        last_signal = 0.0
        last_candle = 0.0
        last_sentiment = 0.0
        last_health = 0.0

        while True:
            now = asyncio.get_event_loop().time()

            if now - last_health >= health_interval:
                await self.health_check_task()
                last_health = now

            if now - last_sentiment >= sentiment_interval:
                await self.sentiment_task()
                last_sentiment = now

            if now - last_candle >= candle_interval:
                await self.candle_ingestion_task()
                last_candle = now

            if now - last_signal >= signal_interval:
                await self.signal_pipeline_task()
                last_signal = now

            await asyncio.sleep(10)


async def run_worker() -> None:
    """Entry point for the worker process."""
    setup_logging()
    cfg = load_config()
    worker = Worker(cfg)
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
