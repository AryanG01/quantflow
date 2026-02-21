-- Migration 004: model_artifacts table for DB-backed ML model persistence.
-- Stores pickled model binaries so the model survives Railway ephemeral filesystem restarts.

CREATE TABLE IF NOT EXISTS model_artifacts (
    model_id   TEXT PRIMARY KEY,
    model_type TEXT NOT NULL,
    artifact   BYTEA NOT NULL,
    metadata   JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
