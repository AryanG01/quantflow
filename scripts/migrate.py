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


def main() -> None:
    """Discover and run all migrations/*.sql files in alphabetical order."""
    setup_logging()
    cfg = load_config()

    logger.info("connecting", host=cfg.database.host, db=cfg.database.name)
    engine = sa.create_engine(cfg.database.url)

    sql_files = sorted(Path("migrations").glob("*.sql"))
    if not sql_files:
        print("No .sql files found in migrations/")
        sys.exit(1)

    print(f"Running {len(sql_files)} migration(s):\n")

    passed = 0
    failed = 0

    for sql_file in sql_files:
        sql = sql_file.read_text()
        statements = _split_sql(sql)
        try:
            with engine.connect() as conn:
                for stmt in statements:
                    conn.execute(sa.text(stmt))
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
