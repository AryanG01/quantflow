# QuantFlow

A production-oriented AI trading system for crypto spot markets, built around a **regime-gated Mixture-of-Experts signal architecture** with uncertainty-aware position sizing.

QuantFlow detects whether the market is trending, mean-reverting, or choppy using a Hidden Markov Model, then dynamically adjusts how it weighs technical analysis, ML predictions, and sentiment signals. When the model is uncertain, it sizes positions smaller. When drawdown hits 15%, it kills all trading.

## How It Works

```
Market Data (Binance, Coinbase)
    │
    ▼
Technical Features (RSI, ATR, Bollinger %B, VWAP, realized vol)
    │
    ├──► LightGBM Quantile Regression (5 quantiles → uncertainty estimate)
    ├──► HMM Regime Detection (3-state: trending / mean-reverting / choppy)
    └──► Sentiment Scoring (CryptoPanic + Reddit, anti-manipulation filtered)
            │
            ▼
    Regime-Gated MoE Signal Fusion
    (regime determines component weights + choppy scales down 70%)
            │
            ▼
    Risk Management
    ├── Vol-targeted position sizing
    ├── Concentration limits (30% max)
    ├── Kill switch (-15% drawdown)
    └── Staleness detection
            │
            ▼
    Execution (Paper → Live)
    └── Order manager with partial fill handling
```

## Key Features

- **Regime-Gated Signals** — A 3-state Gaussian HMM classifies market conditions. Trending markets get heavier ML/technical weights. Choppy markets reduce position size by 70%.
- **Uncertainty-Aware Sizing** — LightGBM quantile regression (q10-q90) provides prediction intervals. Wide intervals → low confidence → smaller positions.
- **Triple-Barrier Labeling** — ML targets are based on which exit condition hits first (profit target, stop loss, or time expiry), not arbitrary return horizons.
- **Walk-Forward Validation** — Strict temporal train/test splits with purge gaps and embargo periods prevent any data leakage.
- **Monte Carlo Robustness** — Block-bootstrap return simulations and parameter perturbation (±20%) generate confidence intervals on strategy performance.
- **Kill Switch** — Hard stop at -15% drawdown. Non-negotiable, cannot be overridden without manual reset.
- **Paper Trading First** — All strategies must run in paper mode before touching live capital.

## Architecture

```
quantflow/
├── packages/           # Domain libraries
│   ├── common/         # Shared types, config, logging
│   ├── data_ingestion/ # Exchange adapters (ccxt), rate limiting, backfill
│   ├── features/       # Technical indicators, rolling z-score normalization
│   ├── models/         # LightGBM quantile, walk-forward training
│   ├── signals/        # HMM regime detection, MoE signal fusion
│   ├── risk/           # Vol-target sizing, risk checks, drawdown monitor
│   ├── execution/      # Order management, paper/live mode
│   ├── backtest/       # Vectorized + event-driven engines, Monte Carlo
│   └── monitoring/     # Prometheus metrics, alerting, drift detection
├── apps/
│   ├── api/            # FastAPI REST backend
│   └── worker/         # Scheduled pipeline (signals every 4h)
├── frontend/           # Next.js trading dashboard
├── scripts/            # CLI tools (backfill, backtest, ablation study)
├── tests/              # 71 unit + integration tests
├── config/             # System configuration (YAML)
├── migrations/         # TimescaleDB schema
└── docker-compose.yml  # Full stack (DB, Redis, Prometheus, Grafana)
```

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Docker + Docker Compose
- Node.js 20+ (for frontend)

### Setup

```bash
# Install Python dependencies
uv sync --all-extras

# Start infrastructure
docker compose -f docker-compose.dev.yml up -d

# Run tests
make test

# Run a backtest on synthetic data
PYTHONPATH=. uv run python scripts/run_backtest.py

# Start the API server
uv run uvicorn apps.api.main:app --reload --port 8000

# Start the frontend (in another terminal)
cd frontend && npm install && npm run dev
```

### Configuration

All configuration lives in `config/default.yaml` with environment variable overrides:

```yaml
universe:
  symbols: [BTC/USDT, ETH/USDT, SOL/USDT]
  timeframe: "4h"

risk:
  max_drawdown_pct: 0.15    # kill switch threshold
  vol_target: 0.15           # 15% annualized target vol
  max_position_pct: 0.25     # max 25% in one position

execution:
  mode: paper                # paper | live
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| ML | LightGBM, scikit-learn, hmmlearn |
| Data | TimescaleDB (Postgres), Redis, Parquet |
| API | FastAPI |
| Frontend | Next.js 15, React 19, Tailwind CSS 4 |
| Exchange | ccxt (Binance, Coinbase) |
| Monitoring | Prometheus, Grafana |
| Infra | Docker, docker-compose |
| Testing | pytest (71 tests) |

## Testing

```bash
make test          # all tests
make test-unit     # unit tests only
make lint          # ruff + mypy
```

## Safety

- API keys and secrets are never committed (`.env` is gitignored)
- Kill switch halts all trading at -15% drawdown
- Paper trading is required before any live capital
- All exchange interactions handle rate limits, partial fills, and API outages
- No strategies that could constitute market manipulation

## License

MIT
