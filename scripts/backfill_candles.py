"""CLI entrypoint for backfilling candle data from exchanges."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import click
import sqlalchemy as sa

from packages.common.config import load_config
from packages.common.logging import get_logger, setup_logging
from packages.data_ingestion.backfill import backfill_candles
from packages.data_ingestion.binance_adapter import BinanceAdapter

logger = get_logger(__name__)


@click.command()
@click.option("--config", "config_path", default="config/default.yaml", help="Config file path")
@click.option("--symbol", default=None, help="Single symbol to backfill (overrides config)")
@click.option("--days", default=None, type=int, help="Lookback days (overrides config)")
@click.option("--exchange", default="binance", type=click.Choice(["binance", "coinbase"]))
def main(
    config_path: str,
    symbol: str | None,
    days: int | None,
    exchange: str,
) -> None:
    """Backfill historical candle data from exchange to TimescaleDB."""
    setup_logging()
    cfg = load_config(config_path)

    symbols = [symbol] if symbol else cfg.universe.symbols
    lookback_days = days if days else cfg.universe.lookback_days
    timeframe = cfg.universe.timeframe

    engine = sa.create_engine(cfg.database.url)
    start = datetime.now(UTC) - timedelta(days=lookback_days)

    async def run() -> None:
        exchange_cfg = cfg.exchanges.get(exchange)
        if exchange_cfg is None:
            logger.error("exchange_not_configured", exchange=exchange)
            return

        adapter = BinanceAdapter(exchange_cfg)
        try:
            for sym in symbols:
                total = await backfill_candles(
                    provider=adapter,
                    engine=engine,
                    symbol=sym,
                    timeframe=timeframe,
                    start=start,
                )
                logger.info("symbol_backfill_done", symbol=sym, total_candles=total)
        finally:
            await adapter.close()

    asyncio.run(run())


if __name__ == "__main__":
    main()
