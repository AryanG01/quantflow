"""Worker process: scheduled tasks for the trading system.

Scheduling:
- Every 4h: signal pipeline (features → predict → regime → fuse → risk → execute)
- Every 5m: sentiment ingestion, orderbook snapshots, order status polling
- Every 1m: health check, drawdown monitoring
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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

    async def sentiment_task(self) -> None:
        """Sentiment ingestion — runs every 5 minutes."""
        logger.debug("sentiment_task_tick")

    async def health_check_task(self) -> None:
        """Health and drawdown monitoring — runs every 1 minute."""
        logger.debug("health_check_tick")

    async def run(self) -> None:
        """Main worker loop with scheduled tasks."""
        logger.info("worker_started", mode=self._config.execution.mode)

        signal_interval = 4 * 60 * 60  # 4 hours
        sentiment_interval = 5 * 60  # 5 minutes
        health_interval = 60  # 1 minute

        last_signal = 0.0
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
