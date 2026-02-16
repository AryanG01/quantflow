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
- [x] Builds cleanly

### Testing ✅
- [x] 72 unit/integration tests, all passing
- [x] Test coverage: cost_model, metrics, technical, normalizer, labeling, walk_forward, regime_detector, signal_fusion, position_sizer, risk_checks, backtest_engine
- [x] Integration test (Binance adapter) excluded from CI (geo-blocked on GitHub runners)

### Repo + Infra ✅
- [x] GitHub repo created: https://github.com/AryanG01/quantflow
- [x] Initial commit pushed (CLAUDE.md excluded via .gitignore)
- [x] README.md with full project description
- [x] PROGRESS.md for tracking

### Worker Pipeline ✅
- [x] `apps/worker/tasks/signal_pipeline.py` — Full SignalPipeline class
- [x] `apps/worker/main.py` — Worker class with DB engine, wired to SignalPipeline

### CI/CD Pipeline ✅
- [x] `.github/workflows/ci.yml` — ruff check + ruff format + mypy + pytest + frontend build
- [x] All 4 Python checks pass (lint, format, typecheck, tests)
- [x] Frontend build check passes
- [x] Integration tests excluded in CI with `-m "not integration"`

### Lint + Type Cleanup ✅
- [x] All ruff lint issues resolved (0 errors)
- [x] All ruff format issues resolved
- [x] All mypy type errors resolved (0 errors, strict mode)
- [x] `(str, Enum)` migrated to `StrEnum` (Python 3.12)
- [x] TC type-checking imports applied (with Pydantic runtime exceptions)
- [x] ML naming convention (X, y) preserved via per-file ignores

### API Demo Data ✅
- [x] FastAPI generates demo data on startup (portfolio, signals, positions, equity curve, regime, risk)
- [x] Dashboard shows populated data without needing Docker/DB
- [x] CORS updated to include port 4000

### Documentation ✅
- [x] `HOW_IT_WORKS.md` — Beginner-friendly guide explaining all algorithms, features, and concepts

---

## Current State of the Website

The dashboard is a **read-only monitoring panel**. It displays:
- Portfolio metrics (equity, cash, PnL, drawdown)
- Trading signals per symbol (direction, strength, confidence)
- Open positions with unrealized PnL
- Market regime (trending / mean-reverting / choppy)
- Risk metrics (kill switch status, concentration, volatility)
- Equity curve chart (90 days)

**What it does NOT do yet:**
- No manual trade placement from the UI
- No wallet/exchange connection from the UI
- No settings page

**Trading modes** (configured in `config/default.yaml`):
- `paper` (default): Simulates trades with fake money
- `live`: Connects to real Binance/Coinbase via API keys in `.env`

**To run with real data**, you need:
1. Docker running: `docker compose -f docker-compose.dev.yml up -d`
2. Backfill data: `PYTHONPATH=. uv run python scripts/backfill_candles.py`
3. Start worker: `PYTHONPATH=. uv run python -m apps.worker.main`
4. Start API: `uv run uvicorn apps.api.main:app --reload --port 8000`
5. Start frontend: `cd frontend && npm run dev`

---

## Next Tasks (in priority order)

### 1. Connect to real exchange data
- Set up Docker (TimescaleDB + Redis)
- Backfill historical candles from Binance
- Run worker to generate live signals

### 2. Additional frontend pages
- Trade history page
- Backtest results page
- Settings/configuration page

### 3. Manual trading controls
- Add buy/sell buttons to the UI
- API endpoints for manual order placement

### 4. Exchange wallet connection
- UI flow for entering API keys
- Connect to real Binance/Coinbase accounts

### 5. Deploy to cloud
- Vercel for frontend
- Docker on a VPS for backend + worker + DB

---

## Architecture Summary

```
QuantFlow/
├── packages/           # Domain libraries
│   ├── common/         # Types, config, logging, errors
│   ├── data_ingestion/ # Exchange adapters, backfill
│   ├── features/       # Technical indicators, normalizer
│   ├── models/         # LightGBM, labeling, walk-forward
│   ├── signals/        # Regime detection, MoE fusion
│   ├── risk/           # Position sizing, risk checks
│   ├── execution/      # Order management, paper/live
│   ├── backtest/       # Vectorized + event-driven engines
│   └── monitoring/     # Prometheus, alerting, drift
├── apps/
│   ├── api/            # FastAPI backend (8 endpoints + demo data)
│   └── worker/         # Scheduled pipeline tasks
│       └── tasks/
│           └── signal_pipeline.py  # Full pipeline orchestration
├── frontend/           # Next.js dashboard (port 4000)
├── scripts/            # CLI tools (backfill, backtest, ablation)
├── tests/              # 72 tests (unit + integration)
├── config/             # YAML config + Prometheus
├── migrations/         # TimescaleDB schema
├── HOW_IT_WORKS.md     # Beginner-friendly algorithm explanations
└── docker-compose.yml  # Full stack deployment
```

## Key Design Decisions
- **Regime-gated MoE**: Different signal weights per market regime (trending/mean-reverting/choppy)
- **Quantile regression**: LightGBM predicts full distribution (5 quantiles) for uncertainty-aware sizing
- **Triple-barrier labeling**: Labels based on trading outcomes, not arbitrary horizons
- **Walk-forward with purge/embargo**: Strict temporal separation prevents data leakage
- **Kill switch at -15% DD**: Non-negotiable safety mechanism
- **Paper mode first**: All execution goes through paper trading before live capital

## Commits (latest first)
- `ef0f960` — Skip integration tests in CI (Binance geo-blocked)
- `0b6c249` — Fix mypy type errors (remove stale type:ignore, fix types)
- `a6882a8` — Apply ruff format to all Python files
- `9bf5f01` — Wire worker pipeline, add equity chart, CI, lint cleanup
- `42e94ab` — Initial commit: QuantFlow AI trading system
