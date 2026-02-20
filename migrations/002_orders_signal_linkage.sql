-- Migration 002: add signal metadata and realized PnL columns to orders table

ALTER TABLE orders ADD COLUMN IF NOT EXISTS signal_strength DOUBLE PRECISION;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS signal_regime   VARCHAR(20);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS realized_pnl    DOUBLE PRECISION DEFAULT 0.0;
