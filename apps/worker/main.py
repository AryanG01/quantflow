"""Worker process: scheduled tasks for the trading system.

Scheduling:
- Every 4h: signal pipeline (features → predict → regime → fuse → risk → execute)
- Every 5m: sentiment ingestion, orderbook snapshots, order status polling
- Every 1m: health check, drawdown monitoring
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from packages.common.config import load_config
from packages.common.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def signal_pipeline_task() -> None:
    """Main signal generation pipeline — runs every 4h."""
    logger.info("signal_pipeline_started", time=datetime.now(timezone.utc).isoformat())
    # Pipeline steps:
    # 1. Fetch latest candles
    # 2. Compute features
    # 3. Run ML prediction
    # 4. Detect regime
    # 5. Fuse signals
    # 6. Risk check
    # 7. Size position
    # 8. Execute (paper or live)
    logger.info("signal_pipeline_completed")


async def sentiment_task() -> None:
    """Sentiment ingestion — runs every 5 minutes."""
    logger.debug("sentiment_task_tick")


async def health_check_task() -> None:
    """Health and drawdown monitoring — runs every 1 minute."""
    logger.debug("health_check_tick")


async def run_worker() -> None:
    """Main worker loop with scheduled tasks."""
    setup_logging()
    cfg = load_config()

    logger.info("worker_started", mode=cfg.execution.mode)

    # Simple scheduling loop (replace with APScheduler for production)
    signal_interval = 4 * 60 * 60  # 4 hours
    sentiment_interval = 5 * 60    # 5 minutes
    health_interval = 60           # 1 minute

    last_signal = 0.0
    last_sentiment = 0.0
    last_health = 0.0

    while True:
        now = asyncio.get_event_loop().time()

        if now - last_health >= health_interval:
            await health_check_task()
            last_health = now

        if now - last_sentiment >= sentiment_interval:
            await sentiment_task()
            last_sentiment = now

        if now - last_signal >= signal_interval:
            await signal_pipeline_task()
            last_signal = now

        await asyncio.sleep(10)


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
