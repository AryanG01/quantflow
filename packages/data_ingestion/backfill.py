"""Paginated candle backfill with idempotent DB upsert."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from packages.common.logging import get_logger
from packages.common.time_utils import timeframe_to_ms
from packages.common.types import Candle
from packages.data_ingestion.interfaces import MarketDataProvider

logger = get_logger(__name__)

CANDLES_TABLE = sa.Table(
    "candles",
    sa.MetaData(),
    sa.Column("time", sa.DateTime(timezone=True), primary_key=True),
    sa.Column("exchange", sa.Text, primary_key=True),
    sa.Column("symbol", sa.Text, primary_key=True),
    sa.Column("timeframe", sa.Text, primary_key=True),
    sa.Column("open", sa.Float),
    sa.Column("high", sa.Float),
    sa.Column("low", sa.Float),
    sa.Column("close", sa.Float),
    sa.Column("volume", sa.Float),
)


def _upsert_candles(engine: Engine, candles: list[Candle]) -> int:
    """Insert candles into DB, skipping duplicates."""
    if not candles:
        return 0

    rows = [
        {
            "time": c.time,
            "exchange": c.exchange,
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]

    stmt = pg_insert(CANDLES_TABLE).values(rows).on_conflict_do_nothing()

    with engine.begin() as conn:
        result = conn.execute(stmt)
        return result.rowcount  # type: ignore[return-value]


async def backfill_candles(
    provider: MarketDataProvider,
    engine: Engine,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime | None = None,
    batch_size: int = 500,
) -> int:
    """Backfill candles from exchange to database.

    Paginates through the exchange API, inserting in batches.
    Idempotent — safe to re-run.

    Returns:
        Total number of new candles inserted.
    """
    if end is None:
        end = datetime.now(timezone.utc)

    start = start.replace(tzinfo=timezone.utc) if start.tzinfo is None else start
    end = end.replace(tzinfo=timezone.utc) if end.tzinfo is None else end

    tf_ms = timeframe_to_ms(timeframe)
    total_inserted = 0
    cursor = start

    logger.info(
        "backfill_started",
        exchange=provider.get_exchange_name(),
        symbol=symbol,
        timeframe=timeframe,
        start=start.isoformat(),
        end=end.isoformat(),
    )

    while cursor < end:
        candles = await provider.fetch_candles(symbol, timeframe, cursor, limit=batch_size)

        if not candles:
            break

        inserted = _upsert_candles(engine, candles)
        total_inserted += inserted

        last_time = candles[-1].time
        cursor = last_time + timedelta(milliseconds=tf_ms)

        logger.debug(
            "backfill_batch",
            symbol=symbol,
            fetched=len(candles),
            inserted=inserted,
            cursor=cursor.isoformat(),
        )

        # Stop if we've reached the end or exchange returned fewer than requested
        if len(candles) < batch_size:
            break

    logger.info(
        "backfill_completed",
        exchange=provider.get_exchange_name(),
        symbol=symbol,
        total_inserted=total_inserted,
    )
    return total_inserted
