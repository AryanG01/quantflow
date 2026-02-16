"""DB-backed portfolio state management."""

from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.engine import Engine

from packages.common.types import PortfolioSnapshot
from packages.risk.interfaces import PortfolioStateStore

PORTFOLIO_TABLE = sa.Table(
    "portfolio_snapshots",
    sa.MetaData(),
    sa.Column("time", sa.DateTime(timezone=True), primary_key=True),
    sa.Column("equity", sa.Float),
    sa.Column("cash", sa.Float),
    sa.Column("positions_value", sa.Float),
    sa.Column("unrealized_pnl", sa.Float),
    sa.Column("realized_pnl", sa.Float),
    sa.Column("drawdown_pct", sa.Float),
)


class DBPortfolioStateStore(PortfolioStateStore):
    """Portfolio state backed by TimescaleDB."""

    def __init__(self, engine: Engine, initial_equity: float = 100_000.0) -> None:
        self._engine = engine
        self._initial_equity = initial_equity

    def get_snapshot(self) -> PortfolioSnapshot:
        """Get the latest portfolio snapshot."""
        query = (
            sa.select(PORTFOLIO_TABLE)
            .order_by(PORTFOLIO_TABLE.c.time.desc())
            .limit(1)
        )

        with self._engine.connect() as conn:
            result = conn.execute(query)
            row = result.fetchone()

        if row is None:
            return PortfolioSnapshot(
                time=datetime.now(timezone.utc),
                equity=self._initial_equity,
                cash=self._initial_equity,
                positions_value=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                drawdown_pct=0.0,
            )

        return PortfolioSnapshot(
            time=row.time,
            equity=row.equity,
            cash=row.cash,
            positions_value=row.positions_value,
            unrealized_pnl=row.unrealized_pnl,
            realized_pnl=row.realized_pnl,
            drawdown_pct=row.drawdown_pct,
        )

    def save_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Save a portfolio snapshot to DB."""
        stmt = sa.insert(PORTFOLIO_TABLE).values(
            time=snapshot.time,
            equity=snapshot.equity,
            cash=snapshot.cash,
            positions_value=snapshot.positions_value,
            unrealized_pnl=snapshot.unrealized_pnl,
            realized_pnl=snapshot.realized_pnl,
            drawdown_pct=snapshot.drawdown_pct,
        )

        with self._engine.begin() as conn:
            conn.execute(stmt)
