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
- [x] Components: MetricCard, SignalPanel, PositionsTable, RiskPanel, RegimeBadge
- [x] API client with polling hooks
- [x] Proxies to FastAPI backend via Next.js rewrites
- [x] Builds cleanly

### Testing ✅
- [x] 71 unit/integration tests, all passing
- [x] Test coverage: cost_model, metrics, technical, normalizer, labeling, walk_forward, regime_detector, signal_fusion, position_sizer, risk_checks, backtest_engine

### Repo + Infra ✅
- [x] GitHub repo created: https://github.com/AryanG01/quantflow
- [x] Initial commit pushed (CLAUDE.md excluded via .gitignore)
- [x] README.md with full project description
- [x] PROGRESS.md for tracking

### Worker Pipeline ✅
- [x] `apps/worker/tasks/signal_pipeline.py` — Full SignalPipeline class
- [x] `apps/worker/main.py` — Worker class with DB engine, wired to SignalPipeline

### Equity Curve Chart ✅
- [x] `frontend/src/components/EquityChart.tsx` — Recharts AreaChart with green/red gradient fill
- [x] Wired into main dashboard page, polls `/api/equity-history` every 15s

### GitHub Actions CI ✅
- [x] `.github/workflows/ci.yml` — ruff + mypy + pytest (Python) + frontend build (Node.js)

### Lint Cleanup ✅
- [x] All ruff issues resolved (0 errors)
- [x] `(str, Enum)` migrated to `StrEnum` (Python 3.12)
- [x] TC type-checking imports applied (with Pydantic runtime exceptions)
- [x] ML naming convention (X, y) preserved via per-file ignores
- [x] 72 tests passing

---

## Next Tasks (in priority order)

### 1. End-to-end integration test
- Test SignalPipeline against a running DB with seeded candle data

### 2. mypy strict cleanup
- Run `uv run mypy packages/ apps/ scripts/` and fix remaining type errors

### 3. Additional frontend pages
- Trade history page
- Backtest results page
- Settings page

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
│   ├── api/            # FastAPI backend (8 endpoints)
│   └── worker/         # Scheduled pipeline tasks
│       └── tasks/
│           └── signal_pipeline.py  # Full pipeline orchestration
├── frontend/           # Next.js dashboard
├── scripts/            # CLI tools (backfill, backtest, ablation)
├── tests/              # 71 tests (unit + integration)
├── config/             # YAML config + Prometheus
├── migrations/         # TimescaleDB schema
└── docker-compose.yml  # Full stack deployment
```

## Key Design Decisions
- **Regime-gated MoE**: Different signal weights per market regime (trending/mean-reverting/choppy)
- **Quantile regression**: LightGBM predicts full distribution (5 quantiles) for uncertainty-aware sizing
- **Triple-barrier labeling**: Labels based on trading outcomes, not arbitrary horizons
- **Walk-forward with purge/embargo**: Strict temporal separation prevents data leakage
- **Kill switch at -15% DD**: Non-negotiable safety mechanism
- **Paper mode first**: All execution goes through paper trading before live capital
