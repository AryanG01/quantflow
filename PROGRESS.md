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

### Hardcoded Logic Removal & Config-Driven Cleanup ✅ (2026-02-20)

All 30+ hardcoded values across the codebase moved to `AppConfig` + `config/default.yaml`:

**Critical fixes (visible bugs):**
- [x] **T1-A** `_persist_risk_metrics()` now computes real portfolio vol & Sharpe from last 90 equity snapshots (was always 0.0/None)
- [x] **T1-B** `orders` table: new columns `signal_strength`, `signal_regime`, `realized_pnl` (migration 002). `_persist_order()` writes signal metadata; `_get_db_trades()` reads them. Sell-side `realized_pnl` computed at fill time.
- [x] **T1-C** Fee model centralized: `0.001` hardcode replaced by `config.exchanges["binance"].fees_bps.taker / 10_000` in both `signal_pipeline.py` and `api/main.py`

**Config-driven parameters:**
- [x] **T2-A** `WorkerConfig` — scheduling intervals (`signal_interval_hours`, `candle_interval_hours`, `sentiment_interval_minutes`, `health_interval_seconds`, `loop_sleep_seconds`, `candle_backfill_hours`, `sentiment_retention_hours`)
- [x] **T2-B** `PortfolioConfig` — `initial_equity`, `signal_lookback_bars`, `min_train_bars`, `min_valid_labels`, `vol_lookback_bars`
- [x] **T2-C** `DEFAULT_REGIME_WEIGHTS` dict removed from `signal_fusion.py`; single source of truth in `SignalFusionConfig.regime_weights` (default_factory)
- [x] **T2-D** CORS origins read from `CORS_ORIGINS` env var (comma-separated) with config fallback; API version from `ApiConfig.version`
- [x] **T2-E** Paper fills apply half-spread slippage from `ExecutionConfig.slippage_model.fixed_spread_bps` (via `OrderManager.slippage_bps`)
- [x] **T2-F** Signal direction threshold `0.05` → `SignalFusionConfig.direction_threshold`
- [x] **T2-G** `_DEMO_PRICES` removed; prices now DB → Binance public API (cached 60s) → empty dict. `_BASE_PRICES` used only for GBM simulation neutral levels. Demo data is lazy (`_get_demo()`)

**Strategy correctness:**
- [x] **T3-A** `realized_vol` annualization uses `TechnicalFeaturesConfig.bars_per_year` (default 2190 = 6×365) instead of magic number
- [x] **T3-B** LightGBM hyperparams (`n_estimators`, `learning_rate`, `max_depth`, `num_leaves`) moved to `ModelConfig`; pipeline passes them through
- [x] **T3-C** `generate_walk_forward_splits` + `run_walk_forward` accept optional `config: WalkForwardConfig` param
- [x] **T3-D** `triple_barrier_labels` accepts optional `config: LabelingConfig`; `neutral_pct` added to `LabelingConfig`
- [x] **T3-E** `CostModelConfig.from_app_config(slippage, fees)` factory added
- [x] **T3-F** `compute_all_metrics` accepts `timeframe` param; derives `bars_per_year` via lookup table; `bars_per_year()` helper added to `metrics.py`
- [x] **T3-G** `SentimentConfig` added to `AppConfig`; `SentimentScorer` initialized from it in `SignalPipeline.__init__`
- [x] **T3-H** New `GET /api/config/universe` endpoint; `Universe` type in frontend api.ts; backtest + trades pages load symbols from API (fallback to hardcoded list)
- [x] **T3-I** `FeaturesConfig.use_orderbook: bool = False` added; default YAML sets it false
- [x] **T3-J** `SignalFusionConfig.confidence_min_iqr` + `confidence_max_iqr` added; wired to `uncertainty_to_confidence()` in pipeline
- [x] **T3-K** `AlertSeverity` enum added with severity-based cooldown (`CRITICAL=0min`, `HIGH=15min`, `MEDIUM=60min`, `LOW=120min`); `AlertRule` uses severity instead of flat `cooldown_minutes`

**New configs added to `AppConfig`:** `WorkerConfig`, `PortfolioConfig`, `ApiConfig`, `SentimentConfig`
**New migration:** `migrations/002_orders_signal_linkage.sql`
**Tests:** 72/72 passing after all changes

### T4 Addons ✅ (2026-02-21)
- [x] **T4-A** Exchange API key UI in Settings (`POST /api/config/exchange/test` — validates live connection)
- [x] **T4-B** Portfolio analytics endpoint (`GET /api/portfolio/analytics`) + Performance card on Dashboard (Sharpe, max drawdown, win rate, avg trade)
- [x] **T4-C** Model retrain trigger (`POST /api/model/retrain`, `GET /api/model/status`) + retrain button in Settings with status polling
- [x] **T4-D** Grafana dashboard (7 panels: equity, drawdown gauge, signals, regime, orders/hr, kill switch, risk rejections); provisioned via `monitoring/grafana/` volume mounts
- [x] **T4-E** Telegram alerts (`AlertSeverity` enum, `send_telegram()`, HIGH/CRITICAL alert routing in `AlertManager`)

**API now has 21 endpoints** (added `portfolio/analytics`, `model/status`, `model/retrain`, `config/exchange/test`, `config/universe`)
**Frontend: 4 pages, all dynamic** (symbols from API, config from API)

### Full Code Review — 50+ Bug Fixes ✅ (2026-02-21)

Comprehensive scan across all layers; fixes committed in 5 batches:

**Batch 1 — Critical Safety (5 fixes):**
- [x] **B1-1** Double fee deduction on sell orders (fees were subtracted twice in portfolio snapshot)
- [x] **B1-2** `KillSwitchError` not caught in `POST /api/orders` → returned HTTP 500 instead of 400
- [x] **B1-3** Dual kill-switch state: alert rule now reads `_risk_checker.kill_switch_active` (not `drawdown_monitor`)
- [x] **B1-4** Orders `INSERT` had no `ON CONFLICT` → `UniqueViolation` on worker restart; changed to `on_conflict_do_nothing()`
- [x] **B1-5** `_retrain_lock` was a `bool` (not thread/async safe); replaced with `asyncio.Lock()`

**Batch 2 — High Backend (9 fixes):**
- [x] **B2-1** `_seen_hashes` set in `SentimentScorer` never pruned → unbounded memory leak
- [x] **B2-2** DB reconnection storm on outage; added 30 s cooldown before retrying `_get_db()`
- [x] **B2-3** `datetime.now(UTC) - tz_naive_timestamp` raised `TypeError`; now coerces to UTC
- [x] **B2-4** Pandas boolean mask used on numpy arrays without `.to_numpy()` → silent index mismatch
- [x] **B2-5** `random.seed(42)` polluted global random state; replaced with `random.Random(42)` instance
- [x] **B2-6** Demo OHLCV candles could have `open > high` or `open < low`; fixed constraints
- [x] **B2-7** `/api/regime` history returned one row per symbol (latest only) instead of time series
- [x] **B2-8** `setup_logging()` was never called in the API process; added to `lifespan()`
- [x] **B2-9** `DrawdownMonitor._peak_equity` reset to 0 on worker restart; now seeded from `MAX(equity)` in DB

**Batch 3 — Backtest Correctness (8 fixes):**
- [x] **B3-1** Turnover formula used `np.diff(returns)` (return volatility) instead of `np.diff(positions)`
- [x] **B3-2** Event-driven engine mark-to-market used `closes[0]` (first bar) instead of actual entry price
- [x] **B3-3** Event-driven engine recorded only cost (no round-trip P&L) → hit rate always 0%
- [x] **B3-4** Triple-barrier tail bars got time-barrier labels from incomplete future windows (lookahead bias)
- [x] **B3-5** `CostModel.maker_fee_bps` was defined but never used; added `is_maker: bool = False` param
- [x] **B3-6** `align_to_bar` epoch was `2000-01-01` (Saturday); corrected to `1970-01-01` (Unix epoch, matches Binance)
- [x] **B3-7** Backfill stopped early on partial Binance batch mid-range; changed to break only on empty response
- [x] **B3-8** PSI drift detector: duplicate percentile edges from sparse features inflated PSI; added `np.unique(edges)`

**Batch 4 — Frontend (9 fixes):**
- [x] **B4-1** `React.ReactNode` used without `React` import in settings/page.tsx
- [x] **B4-2** LIVE badge shown on wrong rows after Sharpe-ratio sort (index-based check was incorrect)
- [x] **B4-3** `max_drawdown` displayed as "NaN%" when null; added null guard + `number | null` type
- [x] **B4-4** `RiskPanel` drawdown bar hardcoded 15% kill-switch threshold; now reads from config
- [x] **B4-5** `orderSymbol`/`symbol` not synced when universe loads; default now set from first API symbol
- [x] **B4-6** Three pages had diverging hardcoded fallback symbol lists; unified via `FALLBACK_SYMBOLS` export
- [x] **B4-7** React key collisions in `PositionsTable` and `SignalPanel`; changed to composite keys
- [x] **B4-8** `SharedHeader` used `health!` non-null assertion; changed to `health?.candle_count`
- [x] **B4-9** `layout.tsx` loaded fonts via Google CDN `<link>`; replaced with `next/font/google`

**Batch 5 — Infrastructure & Naming (10 fixes):**
- [x] **B5-1** `docker-compose.yml` was missing `api` and `worker` service definitions
- [x] **B5-2** `Dockerfile` `COPY models/ models/` failed if directory didn't exist; added `mkdir -p` guard
- [x] **B5-3** Grafana admin password hardcoded to `admin`; now reads `${GRAFANA_ADMIN_PASSWORD:-admin}`
- [x] **B5-4** CI used `npm ci || npm install` fallback which breaks reproducibility; now `npm ci` only
- [x] **B5-5** `ModelRetainResponse` typo (14 occurrences) → renamed to `ModelRetrainResponse`
- [x] **B5-6** `_last_retrain_result` dict missing `"status": "ok"` key on success
- [x] **B5-7** `sentiment_events.title` was nullable in composite PK; added migration 003 (`SET NOT NULL`)
- [x] **B5-8** Grafana datasource variable had empty `"current"` → may not auto-select Prometheus on first load
- [x] **B5-9** `RegimeDetector` accepted any `n_states` but `_map_states_to_regimes` was hardcoded for 3; added guard
- [x] **B5-10** `FillSimulator` in `packages/backtest/simulator.py` was dead code (never imported); removed

**Tests:** 72/72 passing · ruff/mypy clean · frontend build zero errors

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

**Backend API at http://localhost:8000** with 21 endpoints:
- GET: `/api/health`, `/api/signals`, `/api/signals/{symbol}`, `/api/portfolio`, `/api/positions`
- GET: `/api/risk`, `/api/regime`, `/api/equity-history`, `/api/backtest-results`
- GET: `/api/trades`, `/api/config`, `/api/candles/{symbol}`, `/api/prices`, `/api/backtest/history`
- GET: `/api/portfolio/analytics`, `/api/model/status`, `/api/config/universe`
- POST: `/api/orders`, `/api/backtest/run`, `/api/model/retrain`, `/api/config/exchange/test`
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

### 2. Live trading (real capital)
Settings page now has exchange API key fields + connection test (`POST /api/config/exchange/test`). The backend routes exist but live order execution requires valid exchange credentials and switching `paper_mode: false` in config.

### 5. Monitoring dashboards
Grafana dashboard provisioned via `monitoring/grafana/` volume mounts in `docker-compose.yml` (7 panels). Prometheus metrics exported from worker. Run `docker compose up` to activate.

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
