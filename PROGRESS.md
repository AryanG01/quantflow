# QuantFlow — Progress Tracker

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

---

## Pending Tasks

### Immediate
- [ ] GitHub repo creation + initial push
- [ ] Wire worker tasks to call actual pipeline functions end-to-end
- [ ] Add equity curve chart (Recharts LineChart) to frontend
- [ ] Add WebSocket or SSE for real-time frontend updates

### Quality & CI
- [ ] `mypy --strict` full pass (clean up type: ignore comments)
- [ ] `ruff check` full pass
- [ ] GitHub Actions CI pipeline (lint + typecheck + test + backtest regression)
- [ ] Pre-commit hooks (ruff, mypy)

### Production Hardening
- [ ] Grafana dashboard JSON provisioning
- [ ] Add more comprehensive integration tests
- [ ] Load testing for API endpoints
- [ ] Secrets management (vault or env-based)
- [ ] Structured error responses in API
- [ ] Rate limiting on API endpoints
- [ ] Health check endpoint with dependency checks (DB, Redis)

### Feature Enhancements
- [ ] Backtest results page in frontend (table + charts)
- [ ] Trade history page in frontend
- [ ] Settings/config page in frontend
- [ ] Model performance tracking dashboard
- [ ] Multi-symbol correlation matrix view

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
│   ├── api/            # FastAPI backend
│   └── worker/         # Scheduled pipeline tasks
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
