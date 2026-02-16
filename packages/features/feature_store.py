"""Feature store for persisting computed features to DB."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.engine import Engine

FEATURES_TABLE = sa.Table(
    "features",
    sa.MetaData(),
    sa.Column("time", sa.DateTime(timezone=True), primary_key=True),
    sa.Column("symbol", sa.Text, primary_key=True),
    sa.Column("feature_set", sa.Text, primary_key=True),
    sa.Column("features", sa.JSON),
    sa.Column("version", sa.Integer),
)


class FeatureStore:
    """Read/write features to the database."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def write_features(
        self,
        symbol: str,
        feature_set: str,
        features: pd.DataFrame,
        timestamps: pd.Series,  # type: ignore[type-arg]
        version: int = 1,
    ) -> int:
        """Write feature rows to DB. Idempotent via upsert."""
        rows = []
        for i, ts in enumerate(timestamps):
            row_dict = features.iloc[i].dropna().to_dict()
            rows.append(
                {
                    "time": ts,
                    "symbol": symbol,
                    "feature_set": feature_set,
                    "features": json.loads(json.dumps(row_dict, default=str)),
                    "version": version,
                }
            )

        if not rows:
            return 0

        stmt = pg_insert(FEATURES_TABLE).values(rows).on_conflict_do_nothing()
        with self._engine.begin() as conn:
            result = conn.execute(stmt)
            return result.rowcount  # type: ignore[return-value]

    def read_features(
        self,
        symbol: str,
        feature_set: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Read features from DB for a symbol and time range."""
        query = (
            sa.select(FEATURES_TABLE)
            .where(
                sa.and_(
                    FEATURES_TABLE.c.symbol == symbol,
                    FEATURES_TABLE.c.feature_set == feature_set,
                    FEATURES_TABLE.c.time >= start,
                    FEATURES_TABLE.c.time <= end,
                )
            )
            .order_by(FEATURES_TABLE.c.time)
        )

        with self._engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()

        if not rows:
            return pd.DataFrame()

        records = []
        for row in rows:
            feat_dict = row.features if isinstance(row.features, dict) else {}
            feat_dict["time"] = row.time
            records.append(feat_dict)

        return pd.DataFrame(records).set_index("time")
