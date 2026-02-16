-- AI Trading System — Initial Schema
-- TimescaleDB hypertables for time-series data

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ============================================================
-- Market Data
-- ============================================================

CREATE TABLE IF NOT EXISTS candles (
    time        TIMESTAMPTZ NOT NULL,
    exchange    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    timeframe   TEXT        NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time, exchange, symbol, timeframe)
);
SELECT create_hypertable('candles', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_candles_symbol_time ON candles (symbol, time DESC);

CREATE TABLE IF NOT EXISTS orderbook_snapshots (
    time        TIMESTAMPTZ NOT NULL,
    exchange    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    bids        JSONB       NOT NULL,
    asks        JSONB       NOT NULL,
    spread_bps  DOUBLE PRECISION,
    PRIMARY KEY (time, exchange, symbol)
);
SELECT create_hypertable('orderbook_snapshots', 'time', if_not_exists => TRUE);

-- ============================================================
-- Features & Model
-- ============================================================

CREATE TABLE IF NOT EXISTS features (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    feature_set     TEXT        NOT NULL,
    features        JSONB       NOT NULL,
    version         INTEGER     NOT NULL DEFAULT 1,
    PRIMARY KEY (time, symbol, feature_set)
);
SELECT create_hypertable('features', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS model_predictions (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    model_id        TEXT        NOT NULL,
    prediction      JSONB       NOT NULL,  -- {q10, q25, q50, q75, q90, label, confidence}
    PRIMARY KEY (time, symbol, model_id)
);
SELECT create_hypertable('model_predictions', 'time', if_not_exists => TRUE);

-- ============================================================
-- Sentiment
-- ============================================================

CREATE TABLE IF NOT EXISTS sentiment_events (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    source          TEXT        NOT NULL,
    title           TEXT,
    score           DOUBLE PRECISION NOT NULL,
    confidence      DOUBLE PRECISION NOT NULL,
    raw_data        JSONB,
    PRIMARY KEY (time, symbol, source, title)
);
SELECT create_hypertable('sentiment_events', 'time', if_not_exists => TRUE);

-- ============================================================
-- Signals & Execution
-- ============================================================

CREATE TABLE IF NOT EXISTS signals (
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    direction       TEXT        NOT NULL,  -- long, short, flat
    strength        DOUBLE PRECISION NOT NULL,
    confidence      DOUBLE PRECISION NOT NULL,
    regime          TEXT        NOT NULL,
    components      JSONB       NOT NULL,  -- {technical, ml, sentiment}
    PRIMARY KEY (time, symbol)
);
SELECT create_hypertable('signals', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS orders (
    id              TEXT        PRIMARY KEY,
    time            TIMESTAMPTZ NOT NULL,
    symbol          TEXT        NOT NULL,
    exchange        TEXT        NOT NULL,
    side            TEXT        NOT NULL,  -- buy, sell
    order_type      TEXT        NOT NULL,  -- market, limit
    quantity        DOUBLE PRECISION NOT NULL,
    price           DOUBLE PRECISION,
    status          TEXT        NOT NULL,  -- pending, filled, partial, cancelled, rejected
    filled_qty      DOUBLE PRECISION DEFAULT 0,
    avg_fill_price  DOUBLE PRECISION,
    fees            DOUBLE PRECISION DEFAULT 0,
    signal_id       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_orders_symbol_time ON orders (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);

CREATE TABLE IF NOT EXISTS positions (
    symbol          TEXT        PRIMARY KEY,
    exchange        TEXT        NOT NULL,
    side            TEXT        NOT NULL,  -- long, short, flat
    quantity        DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_entry_price DOUBLE PRECISION,
    unrealized_pnl  DOUBLE PRECISION DEFAULT 0,
    realized_pnl    DOUBLE PRECISION DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Portfolio & Risk
-- ============================================================

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    time            TIMESTAMPTZ NOT NULL,
    equity          DOUBLE PRECISION NOT NULL,
    cash            DOUBLE PRECISION NOT NULL,
    positions_value DOUBLE PRECISION NOT NULL,
    unrealized_pnl  DOUBLE PRECISION NOT NULL,
    realized_pnl    DOUBLE PRECISION NOT NULL,
    drawdown_pct    DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (time)
);
SELECT create_hypertable('portfolio_snapshots', 'time', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS risk_metrics (
    time                TIMESTAMPTZ NOT NULL,
    max_drawdown_pct    DOUBLE PRECISION NOT NULL,
    current_drawdown_pct DOUBLE PRECISION NOT NULL,
    portfolio_vol       DOUBLE PRECISION NOT NULL,
    sharpe_ratio        DOUBLE PRECISION,
    concentration_pct   DOUBLE PRECISION NOT NULL,
    kill_switch_active  BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (time)
);
SELECT create_hypertable('risk_metrics', 'time', if_not_exists => TRUE);
