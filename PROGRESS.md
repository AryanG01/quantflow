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
- [x] **Trades page** — Order entry panel (paper mode), buy/sell with market/limit types, filterable trade history, PnL summary cards
- [x] **Backtest page** — Run backtests with strategy/symbol/lookback selection, progress bar, strategy comparison table with LIVE badges
- [x] **Settings page** — Editable universe/risk/execution with sliders and toggles, read-only advanced sections, save/reset to YAML

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

### Frontend Interactive Features ✅
- [x] **Order placement** — `POST /api/orders` with paper-mode OrderManager, fills at latest prices
- [x] **Backtest runner** — `POST /api/backtest/run` with real vectorized engine, DB candles or synthetic GBM fallback
- [x] **Config save/reset** — `PATCH /api/config` persists universe/risk/execution to `config/default.yaml`
- [x] **LIVE/DEMO/OFFLINE indicator** — SharedHeader shows green/amber/red dot based on DB connection status
- [x] **Demo data fallback** — `_generate_demo_data()` with seed 42, all endpoints fall back gracefully

### Worker → DB Writes ✅ (wired — server restart required to activate)
- [x] `DBPortfolioStateStore` replaces in-memory floats — portfolio state persists to `portfolio_snapshots`
- [x] `_persist_signal()` — INSERTs into `signals` table after every fusion step
- [x] `_persist_order()` — INSERTs into `orders` table after every execution
- [x] `_persist_position()` — UPSERTs into `positions` table (ON CONFLICT by symbol)
- [x] `_persist_risk_metrics()` — INSERTs into `risk_metrics` every minute via health_check_task
- [x] Portfolio cash/equity updated after fills (10 bps fee model)
- [x] `ModelRegistry.save()` after training + `load()` at startup (restarts skip retraining)
- [x] `SentimentScorer.compute_score()` replaces hardcoded `sentiment: 0.0`
- [x] Worker: `candle_ingestion_task()` runs every 1h via `BinanceAdapter` + `backfill_candles()`
- [x] Worker: `health_check_task()` calls `_persist_risk_metrics()` every 1 min
- [x] Worker: `sentiment_task()` clears stale events (>24h) every 5 min
- [x] API: `GET /api/backtest-results` returns `_backtest_history` first, demo as fallback
- [x] API: `POST /api/orders` pre-trade risk gate via `RiskChecker.check_pre_trade()`

### Cloud Deployment ✅
- [x] `railway.json` — Railway service config: DOCKERFILE builder, uvicorn start, `/api/health` healthcheck
- [x] `Dockerfile` — `ENV PYTHONPATH=/app` added so `packages/` and `apps/` resolve in Railway containers
- [x] `frontend/next.config.ts` — Uses `NEXT_PUBLIC_API_URL` env var (fallback: `http://localhost:8000`)
- [x] Equity curve fix — `signal_pipeline.run()` writes a portfolio snapshot every cycle, not just on fills
- [ ] Timescale Cloud service created + migrations run (manual step)
- [ ] Railway API service deployed (`DATABASE_URL` env var set)
- [ ] Railway Worker service deployed (same repo, custom start command)
- [ ] Vercel frontend deployed (`NEXT_PUBLIC_API_URL` env var set)

### Documentation ✅
- [x] `HOW_IT_WORKS.md` — Beginner-friendly guide (16 sections: algorithms, dashboard pages, data sources, quick start)
- [x] `PROGRESS.md` — This file

---

## Current State

**Website runs locally at http://localhost:4000** with 4 interactive pages:
- **Dashboard** (`/`) — 6 metric cards with icons, equity chart (time range selector), signals, positions, risk panel, regime badge, system info
- **Trades** (`/trades`) — Paper order entry (buy/sell, market/limit), trade history with filters (all/winners/losers/symbol), 4 summary cards
- **Backtest** (`/backtest`) — Run backtests with symbol/strategy/lookback/capital selection, progress bar, strategy comparison with LIVE badges, methodology note
- **Settings** (`/settings`) — Editable universe/risk/execution with sliders and toggles, read-only advanced sections (features/model/regime), save/reset to YAML

**Backend API at http://localhost:8000** with 16 endpoints:
- GET: `/api/health`, `/api/signals`, `/api/signals/{symbol}`, `/api/portfolio`, `/api/positions`
- GET: `/api/risk`, `/api/regime`, `/api/equity-history`, `/api/backtest-results`
- GET: `/api/trades`, `/api/config`, `/api/candles/{symbol}`, `/api/prices`, `/api/backtest/history`
- POST: `/api/orders`, `/api/backtest/run`
- PATCH: `/api/config`

**Data flow**: API queries DB first → if empty, serves demo data (seed 42) → frontend polls every 5-15s
- Header shows **LIVE** (green) / **DEMO** (amber) / **OFFLINE** (red) status

**What works with real data (when DB is connected):**
- Candle data (BTC/ETH/SOL 4h bars, 2 years, 13,140 candles)
- Live prices from latest candles
- Config from actual YAML file
- Backtests run on real historical candles
- Orders persist to the `orders` table

**What still uses demo data (worker writes implemented — restart API + worker to activate):**
- Portfolio snapshots, signals, positions, risk metrics, equity curve, trades, regime
- Switch to LIVE after: (1) restart API, (2) start worker, (3) wait one pipeline tick (~4h) or run backfill

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

## Remaining Gaps (from original SPEC.md)

### 1. Restart API server (immediate — unblocks backtest/run 404)
The running uvicorn process uses stale code. Code is correct (21 routes verified). Kill and restart.
```bash
# Kill: Ctrl+C on uvicorn terminal, then:
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000
```

### 2. Live exchange connection
No UI for API key entry. No paper → live mode switch from the frontend (the Settings page has a paper/live toggle, but switching to "live" without exchange credentials does nothing).

### 4. Live exchange connection
No UI for API key entry. No paper → live mode switch from the frontend (the Settings page has a paper/live toggle, but switching to "live" without exchange credentials does nothing).

### 5. Monitoring dashboards
Prometheus metrics are exported from the worker, but Grafana dashboards are not configured. `docker-compose.yml` includes Grafana but no provisioned dashboards.

### 6. Cloud deployment
No Vercel/Railway deployment yet.
- Frontend → Vercel (free tier)
- Backend + DB → Railway or Render (free Postgres + containers)

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
│   ├── api/            # FastAPI backend (16 endpoints, DB-connected)
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
