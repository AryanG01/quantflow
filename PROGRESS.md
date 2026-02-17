# QuantFlow — Progress Tracker

## Repo: https://github.com/AryanG01/quantflow

## Completed

### Phase 1 — Data Ingestion + Baseline Backtest ✅
- [x] Project scaffolding (pyproject.toml, Makefile, docker-compose, migrations, config)
- [x] Common package (types, config, logging, errors, time_utils)
- [x] Data ingestion (Binance + Coinbase adapters, rate limiter, backfill)
- [x] Vectorized backtest engine (cost model, metrics, benchmarks, report)
- [x] Tests: 27 passing (cost_model, metrics, backtest_engine)

### Phase 2 — Feature Engineering + ML Baseline ✅
- [x] Features package (technical indicators, orderbook placeholder, normalizer, feature store, registry)
- [x] Models package (LightGBM quantile regression, triple-barrier labeling, walk-forward training, model registry, drift detector)
- [x] Tests: 17 added (technical, normalizer, labeling, walk_forward)

### Phase 3 — Regime Detection + Risk + Signal Fusion ✅
- [x] Signals package (HMM regime detector, regime-gated MoE fusion, confidence mapping)
- [x] Risk package (vol-target position sizer, risk checks, drawdown monitor, portfolio state)
- [x] Tests: 22 added (regime_detector, signal_fusion, position_sizer, risk_checks)

### Phase 4 — Sentiment + Execution + Monitoring ✅
- [x] Sentiment scorer with anti-manipulation filters
- [x] Execution package (Binance + Coinbase executors, order manager with paper mode, slippage model)
- [x] Monitoring (Prometheus metrics exporter, alerting rules, drift monitor)
- [x] Worker process with scheduled tasks
- [x] FastAPI backend with CORS and REST endpoints
- [x] Full docker-compose.yml (TimescaleDB, Redis, Prometheus, Grafana)

### Phase 5 — Event-Driven Backtest + Robustness ✅
- [x] Event-driven backtest engine (BAR_CLOSE → SIGNAL → ORDER → FILL)
- [x] Fill simulator (partial fills, latency, spread crossing)
- [x] Monte Carlo bootstrap (block resampling, parameter perturbation)
- [x] Ablation study script
- [x] Vectorized engine preserved as engine_vectorized.py

### Phase 6 — Deployment Scaffolding ✅
- [x] Multi-stage Dockerfile (api + worker targets)
- [x] Backtest runner script with Monte Carlo

### Frontend Dashboard ✅
- [x] Next.js 15 + React 19 + Tailwind 4
- [x] Terminal-inspired dark theme (industrial/utilitarian aesthetic)
- [x] Components: MetricCard, SignalPanel, PositionsTable, RiskPanel, RegimeBadge, EquityChart
- [x] API client with polling hooks
- [x] Proxies to FastAPI backend via Next.js rewrites (port 4000 → 8000)

### Frontend Multi-Page Navigation ✅
- [x] NavBar component with active-state highlighting (Dashboard, Trades, Backtest, Settings)
- [x] SharedHeader extracted into layout for consistent branding + nav across all pages
- [x] **Trades page** — Filterable trade history table with PnL summary cards, regime color-coding
- [x] **Backtest page** — Strategy comparison table ranked by Sharpe, methodology footer
- [x] **Settings page** — Recursive config tree renderer with type-colored values (read-only)

### Real Database Integration ✅
- [x] Docker: TimescaleDB + Redis running via docker-compose.dev.yml
- [x] Migrations auto-run on container start (10 tables created)
- [x] Backfilled 13,140 real candles from Binance (BTC/ETH/SOL, 2 years of 4h bars)
- [x] API wired to TimescaleDB — queries DB first, falls back to demo data
- [x] New endpoints: `/api/candles/{symbol}`, `/api/prices` (real market data)
- [x] `/api/config` reads from real `config/default.yaml` (not hardcoded)
- [x] `/api/health` shows `db_connected` status + `candle_count`
- [x] Header shows DB connection status + candle count
- [x] Backfill script supports `--no-sandbox` flag for real Binance data

### Testing ✅
- [x] 72 unit/integration tests, all passing
- [x] Integration test (Binance adapter) excluded from CI (geo-blocked on GitHub runners)

### CI/CD Pipeline ✅
- [x] `.github/workflows/ci.yml` — ruff check + ruff format + mypy + pytest + frontend build
- [x] All checks pass on GitHub Actions

### Documentation ✅
- [x] `HOW_IT_WORKS.md` — Beginner-friendly guide explaining all algorithms
- [x] `PROGRESS.md` — This file

---

## Current State

**Website runs locally at http://localhost:4000** with 4 pages:
- **Dashboard** (`/`) — Portfolio metrics, signals, equity chart, positions, risk, regime
- **Trades** (`/trades`) — Filterable trade history with PnL summary
- **Backtest** (`/backtest`) — Strategy comparison table
- **Settings** (`/settings`) — Read-only config display

**Backend API at http://localhost:8000** with 12 endpoints:
- `/api/health`, `/api/signals`, `/api/portfolio`, `/api/positions`
- `/api/risk`, `/api/regime`, `/api/equity-history`, `/api/backtest-results`
- `/api/trades`, `/api/config`, `/api/candles/{symbol}`, `/api/prices`

**Database**: 13,140 real candles in TimescaleDB. Other tables (signals, positions, portfolio_snapshots, orders, risk_metrics) are empty — populated once the worker runs.

**Data flow**: API queries DB first → if empty, serves demo data → frontend polls every 5-15s

**What currently works with REAL data:**
- Candle data (BTC/ETH/SOL 4h bars, 2 years)
- Live prices from latest candles
- Config from actual YAML file

**What still uses DEMO data (until worker runs):**
- Portfolio, signals, positions, risk metrics, equity curve, trades, regime, backtest results

---

## How to Run

```bash
# 1. Start database (requires Docker Desktop running)
docker compose -f docker-compose.dev.yml up -d

# 2. Backfill candles (only needed once — data persists in Docker volume)
PYTHONPATH=. uv run python scripts/backfill_candles.py --no-sandbox

# 3. Start API
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000

# 4. Start frontend
cd frontend && npm run dev

# Visit http://localhost:4000
```

---

## Next Tasks (in priority order)

### 1. Make frontend dynamic (replace hardcoded/demo data)
**Settings page** — Replace read-only config display with interactive controls:
- Dropdowns to select symbols, timeframe, exchange
- Sliders for risk params (vol_target, max_drawdown, max_position)
- POST endpoint to save config changes
- Live validation

**Backtest page** — Make backtests runnable from the UI:
- Form to select strategy, symbol, date range
- POST endpoint to trigger backtest
- Real-time progress indicator
- Display actual results (not hardcoded)

**Trades page** — Enable paper trading from the UI:
- Buy/sell form with symbol, quantity, order type
- POST endpoint for order placement
- Real-time order status updates
- Position management (close positions)

### 2. Run worker for live signal generation
- Start worker process to compute features → train models → generate signals
- Signals, positions, portfolio snapshots populate in DB
- Dashboard switches from demo to real data automatically

### 3. Exchange wallet connection
- UI flow for entering API keys securely
- Connect to real Binance/Coinbase accounts
- Switch between paper and live modes

### 4. Deploy to cloud (free hosting)
- Frontend → Vercel (free tier)
- Backend + DB → Railway or Render (free Postgres + containers)
- Site stays up when laptop is closed

---

## Architecture Summary

```
QuantFlow/
├── packages/           # Domain libraries (Python)
│   ├── common/         # Types, config, logging, errors
│   ├── data_ingestion/ # Exchange adapters, backfill
│   ├── features/       # Technical indicators, normalizer
│   ├── models/         # LightGBM, labeling, walk-forward
│   ├── signals/        # Regime detection, MoE fusion, sentiment
│   ├── risk/           # Position sizing, risk checks, kill switch
│   ├── execution/      # Order management, paper/live modes
│   ├── backtest/       # Vectorized + event-driven engines
│   └── monitoring/     # Prometheus, alerting, drift detection
├── apps/
│   ├── api/            # FastAPI backend (12 endpoints, DB-connected)
│   └── worker/         # Scheduled pipeline tasks
├── frontend/           # Next.js 15 dashboard (port 4000)
├── scripts/            # CLI tools (backfill, backtest, ablation)
├── tests/              # 72 tests (unit + integration)
├── config/             # YAML config + Prometheus
├── migrations/         # TimescaleDB schema (10 tables)
└── docker-compose.dev.yml  # TimescaleDB + Redis
```

## Commits (latest first)
- `f2e76f9` — Wire API to real TimescaleDB, add candles/prices endpoints
- `01e8b60` — Update PROGRESS.md with frontend navigation milestone
- `00836b2` — Add frontend navigation, trades/backtest/settings pages
- `17d113a` — Add demo data, HOW_IT_WORKS docs, update PROGRESS tracking
- `ef0f960` — Skip integration tests in CI (Binance geo-blocked)
- `0b6c249` — Fix mypy type errors (remove stale type:ignore, fix types)
- `a6882a8` — Apply ruff format to all Python files
- `9bf5f01` — Wire worker pipeline, add equity chart, CI, lint cleanup
- `42e94ab` — Initial commit: QuantFlow AI trading system
