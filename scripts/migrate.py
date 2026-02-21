"""Run all pending SQL migrations against the configured database."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path when the script is run directly
# (Python sets sys.path[0] to the script's directory, not the CWD).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlalchemy as sa

from packages.common.config import load_config
from packages.common.logging import get_logger, setup_logging

logger = get_logger(__name__)


def _split_sql(sql: str) -> list[str]:
    """Split a SQL file into individual executable statements.

    Splits on ';' and skips chunks that contain only SQL comments or whitespace,
    which handles the comment separators between blocks in migration files.
    """
    statements = []
    for chunk in sql.split(";"):
        # Strip lines that are purely SQL comments to check if real SQL remains.
        non_comment = "\n".join(
            line for line in chunk.splitlines() if not line.strip().startswith("--")
        ).strip()
        if non_comment:
            statements.append(chunk.strip())
    return statements


def _ensure_migrations_table(engine: sa.engine.Engine) -> None:
    """Ensure the schema_migrations tracking table exists."""
    with engine.connect() as conn:
        conn.execute(
            sa.text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename   TEXT        PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.commit()


def _get_applied_migrations(engine: sa.engine.Engine) -> set[str]:
    """Return the set of already-applied migration filenames."""
    with engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT filename FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def _record_migration(conn: sa.engine.Connection, filename: str) -> None:
    """Record a successfully applied migration."""
    conn.execute(
        sa.text("INSERT INTO schema_migrations (filename) VALUES (:fn) ON CONFLICT DO NOTHING"),
        {"fn": filename},
    )


def main() -> None:
    """Discover and run all migrations/*.sql files in alphabetical order.

    Already-applied migrations (tracked in schema_migrations table) are skipped.
    """
    setup_logging()
    cfg = load_config()

    logger.info("connecting", host=cfg.database.host, db=cfg.database.name)
    engine = sa.create_engine(cfg.database.url)

    _ensure_migrations_table(engine)
    applied = _get_applied_migrations(engine)

    sql_files = sorted(Path("migrations").glob("*.sql"))
    if not sql_files:
        print("No .sql files found in migrations/")
        sys.exit(1)

    print(f"Found {len(sql_files)} migration(s):\n")

    passed = 0
    failed = 0

    for sql_file in sql_files:
        if sql_file.name in applied:
            print(f"  ─  {sql_file.name}  (already applied, skipping)")
            passed += 1
            continue

        sql = sql_file.read_text()
        statements = _split_sql(sql)
        try:
            with engine.connect() as conn:
                for stmt in statements:
                    conn.execute(sa.text(stmt))
                _record_migration(conn, sql_file.name)
                conn.commit()
            print(f"  ✓  {sql_file.name}")
            passed += 1
        except Exception as exc:
            print(f"  ✗  {sql_file.name}  —  {exc}")
            logger.exception("migration_failed", file=sql_file.name)
            failed += 1

    print(f"\n{passed} succeeded, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
