"""Worker process: scheduled tasks for the trading system.

Scheduling (all intervals are config-driven via AppConfig.worker):
- Every signal_interval_hours: signal pipeline (features → predict → regime → fuse → risk → execute)
- Every candle_interval_hours: candle ingestion (backfill recent candles from exchange)
- Every sentiment_interval_minutes: sentiment cleanup
- Every health_interval_seconds: health check, drawdown monitoring, risk metrics persistence
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
        """Main signal generation pipeline — runs every signal_interval_hours."""
        logger.info("signal_pipeline_started", time=datetime.now(UTC).isoformat())
        try:
            await self._pipeline.run()
            logger.info("signal_pipeline_completed")
        except Exception as e:
            logger.error("signal_pipeline_failed", error=str(e))

    async def candle_ingestion_task(self) -> None:
        """Backfill recent candles from exchange — runs every candle_interval_hours."""
        try:
            from packages.common.config import ExchangeConfig
            from packages.data_ingestion.backfill import backfill_candles
            from packages.data_ingestion.binance_adapter import BinanceAdapter

            exchange_cfg = self._config.exchanges.get("binance", ExchangeConfig())
            adapter = BinanceAdapter(config=exchange_cfg)
            backfill_hours = self._config.worker.candle_backfill_hours
            start = datetime.now(UTC) - timedelta(hours=backfill_hours)

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
            err = str(e)
            if "418" in err or "banned" in err.lower():
                logger.warning("candle_ingestion_rate_limited", error=err[:120])
            else:
                logger.warning("candle_ingestion_failed", error=err)

    async def sentiment_task(self) -> None:
        """Sentiment cleanup — runs every sentiment_interval_minutes.

        Clears stale events from the in-memory scorer.
        Full ingestion (CryptoPanic/Reddit) requires API keys and is a separate concern.
        """
        try:
            retention_hours = self._config.worker.sentiment_retention_hours
            cutoff = datetime.now(UTC) - timedelta(hours=retention_hours)
            removed = self._pipeline._sentiment_scorer.clear_old_events(cutoff)
            if removed > 0:
                logger.debug("sentiment_stale_events_cleared", count=removed)
        except Exception as e:
            logger.warning("sentiment_task_failed", error=str(e))

    async def health_check_task(self) -> None:
        """Health and drawdown monitoring — runs every health_interval_seconds.

        Persists current risk metrics so the API dashboard stays fresh
        between pipeline runs.
        """
        try:
            self._pipeline._persist_risk_metrics()
        except Exception as e:
            logger.warning("health_check_failed", error=str(e))

    async def run(self) -> None:
        """Main worker loop with config-driven scheduled tasks."""
        logger.info("worker_started", mode=self._config.execution.mode)

        wcfg = self._config.worker
        signal_interval = wcfg.signal_interval_hours * 3600
        candle_interval = wcfg.candle_interval_hours * 3600
        sentiment_interval = wcfg.sentiment_interval_minutes * 60
        health_interval = wcfg.health_interval_seconds

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

            await asyncio.sleep(wcfg.loop_sleep_seconds)


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
