-- Migration 005: idempotency tracking table
-- Bootstraps the schema_migrations table so the runner can skip already-applied files.
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   TEXT        PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
