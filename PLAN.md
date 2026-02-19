# QuantFlow — Active Plan

**Date:** 2026-02-19
**Status:** Worker DB wiring complete. One restart required to unblock frontend.

---

## Immediate Fix Required: Restart the API Server

**Root cause of `POST /api/backtest/run 404`:**
The running uvicorn process at port 8000 is executing **stale code**. It was started before the backtest/order routes were added. The code is correct — a fresh Python import confirms all 21 routes register without error.

```bash
# Fix: kill the running uvicorn and restart
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000
```

After restart, `/api/backtest/run`, `/api/backtest/history`, and `/api/orders` will all work.

---

## What Was Done This Session

### Files Modified
| File | Change |
|------|--------|
| `apps/worker/tasks/signal_pipeline.py` | DB writes for signals/orders/positions/portfolio/risk; model persistence; sentiment wired |
| `apps/worker/main.py` | candle_ingestion_task (1h), health_check_task (1m), sentiment_task (5m) |
| `apps/api/main.py` | backtest-results bug fix (1 line); order risk gate via RiskChecker |

### What This Unlocks (after API restart + worker running)
- `GET /api/signals` → real signals from worker pipeline
- `GET /api/portfolio` → real equity from `portfolio_snapshots`
- `GET /api/equity-history` → real curve from snapshots
- `GET /api/trades` → real filled orders
- `GET /api/risk` → real drawdown/concentration/kill-switch
- `GET /api/positions` → real open positions
- `GET /api/regime` → derived from real signals
- Header shows **LIVE** (green) instead of **DEMO** (amber)

---

## Full Startup Sequence

```bash
# Terminal 1 — DB (if not already running)
docker compose -f docker-compose.dev.yml up -d

# Terminal 2 — API (restart required)
PYTHONPATH=. uv run uvicorn apps.api.main:app --reload --port 8000

# Terminal 3 — Worker
PYTHONPATH=. uv run python -m apps.worker.main

# Terminal 4 — Frontend
cd frontend && npm run dev

# Visit http://localhost:4000
```

Worker runs pipeline immediately on start (last_signal=0.0 means first loop fires all tasks).
After ~2 min: health_check writes risk_metrics → /api/risk goes LIVE.
After first pipeline tick: signals/portfolio/orders written → dashboard goes LIVE.

---

## Remaining Work (Prioritized)

### P1 — Verify Worker→DB in practice
After restart, confirm:
```bash
curl http://localhost:8000/api/signals          # should return real data, not demo
curl http://localhost:8000/api/portfolio        # real equity, not $100k demo
curl http://localhost:8000/api/health           # db_connected: true
```

### P2 — Grafana Dashboards
`docker-compose.yml` includes Grafana but no provisioned dashboards.
Add `grafana/provisioning/dashboards/` with JSON for: equity curve, drawdown, signal strength, order flow.

### P3 — Cloud Deployment
- Frontend → Vercel (free tier, push repo)
- Backend + DB → Railway (free Postgres + containers)
- Required: env vars for DB URL, disable `--reload`

### P4 — Live Exchange Connection
Settings page has paper/live toggle — wiring it to real exchange requires:
- API key entry UI (masked input in Settings)
- Store encrypted in `config/default.yaml` or env
- Switch `OrderManager(paper_mode=False)` when keys are set

---

## Key Architecture Facts
- Signal pipeline: every 4h — candles → features → ML → regime → fuse → risk → execute → write DB
- Health check: every 1m — writes risk_metrics (keeps risk panel fresh between pipeline runs)
- Candle ingestion: every 1h — backfills recent 2h from Binance
- Demo fallback: `db_result or demo_data` pattern in all API endpoints — no frontend changes needed
- Kill switch: -15% drawdown triggers `KillSwitchError`, blocks all future trades until reset
- Model persistence: `models/lightgbm_latest/` — worker skips retraining on restart if file exists

## Test Command
```bash
uv run pytest tests/ -v   # 72 tests, all must pass
```
