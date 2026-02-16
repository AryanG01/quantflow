# AI Trading System — Full Specification

This document contains the complete project specification and requirements for the AI trading system.
It was originally in CLAUDE.md and has been preserved here as the authoritative design brief.

---

You are Claude Code acting as: (1) an expert quantitative trader, (2) an applied AI researcher, and (3) a senior product architect.

Goal: Produce a complete, production-ready AI trading system concept + implementation plan for stocks and/or crypto that a serious solo builder (or small startup) can realistically build. This is NOT generic trading advice. It must be software-architecture-first, risk-aware, and technically implementable.

Hard rules:
- Be explicit about assumptions, data sources, latency constraints, costs, and realistic failure modes.
- Do NOT handwave "alpha." Make each component's purpose testable.
- Keep it buildable: prioritize robust engineering, reproducibility, and safety controls.
- Provide a clear module breakdown, APIs, data schemas, and pseudocode.
- Prefer open-source + widely-used libraries when possible.
- Include compliance-minded notes (KYC/AML for exchanges, regional constraints, market manipulation avoidance). Keep it practical, not legal advice.
- If something is likely infeasible (e.g., true latency arb without coloc), say so and propose a realistic alternative edge.

Scope selection (do this first):
1) Choose ONE primary market focus for the MVP:
   - Crypto spot (multi-exchange) OR crypto perp (single exchange) OR US equities (broker API).
2) Choose the trading frequency for MVP:
   - 5–30 min bars (intraday) OR 1–4h bars (swing) OR market-making-like (only if realistic).
3) State why this scope is feasible for a solo builder given infrastructure constraints.

Deliverable format requirements:
- Extremely structured with clear headings and subheadings.
- Concise but technically deep.
- Provide concrete artifacts: module tree, interfaces, schemas, pseudocode, experiment plan, MVP roadmap, scaling roadmap.
- Where you "research," do it by citing well-known, verifiable concepts and pointing to typical datasets/APIs; do not invent papers. You may reference canonical ideas (e.g., walk-forward validation, triple barrier labeling, HMM regimes) without fake citations.

=========================================================
OUTPUT SECTIONS (MUST FOLLOW THIS ORDER)
=========================================================

## 0) Executive Summary (1 page max)
- One-paragraph system overview.
- The "unique angle" (novel differentiation) in 3 bullets.
- What instruments, timeframe, and strategy family.
- What the system outputs (signals, allocations, orders) and key guardrails.

## 1) Research-Backed Strategy Design (Hybrid, Multi-Component)
Design a hybrid strategy that combines at minimum:
A) Statistical/technical signals
B) ML prediction component
C) Regime/volatility detection
D) Sentiment component (news/social) OR on-chain (if crypto) — choose the most defensible
E) Optional: arbitrage scanner (cross-exchange or triangular) OR funding/basis (if perp) — but only if realistic

For EACH component:
- Purpose: what market inefficiency it targets.
- Inputs: exact features and data requirements.
- Output: signal format (e.g., expected return, probability, score).
- Update frequency + latency sensitivity.
- Failure modes + how to detect them.

Then explain how components fuse together:
- Provide an ensemble / gating design (e.g., regime-gated mixture of experts).
- Show how conflicts are resolved (e.g., arbitration rules, meta-model, or risk-budget weighting).
- Provide a diagram in text (boxes/arrows) plus brief narrative.

### 1.1 Technical Indicator Layer
- Specify a small but strong set of indicators (avoid indicator soup).
- Include at least one microstructure-aware feature if you use order books (e.g., imbalance, spread).
- Explain feature normalization + leakage avoidance.

### 1.2 ML Prediction Layer (Modern + Practical)
Pick one primary approach (choose ONE and justify):
- Gradient boosting on engineered features (strong baseline), OR
- Sequence model (Temporal CNN / lightweight transformer) if data supports it, OR
- Probabilistic model for uncertainty (e.g., quantile regression)
Requirements:
- Define prediction target precisely (next-period return distribution, direction, volatility).
- Labeling method (e.g., triple-barrier / horizon labeling).
- Uncertainty usage (position sizing / risk scaling).
- Walk-forward training plan + drift monitoring.

### 1.3 Regime / Volatility Detection
Implement regime switching using ONE:
- HMM on returns/volatility, OR
- Change-point detection, OR
- Volatility clustering (e.g., realized vol + thresholds)
Define:
- Regimes (e.g., trend, mean-revert, high-vol chop).
- How regime changes alter strategy weights, risk limits, and execution style.

### 1.4 Sentiment / Alternative Data
Choose sources based on market focus:
- Crypto: news + X/Reddit + optional on-chain metrics (active addresses, exchange inflows).
- Equities: news + earnings calendar + sector ETF flows (if available).
Define:
- Ingestion method, rate limits, and cost.
- NLP pipeline (embedding model choice, classifier, topic filters).
- Anti-manipulation heuristics (bot detection proxies, source credibility weighting).
- How sentiment becomes a numeric factor with lag controls.

### 1.5 Arbitrage / Cross-Venue Component (Only If Realistic)
If you include arbitrage:
- Clearly distinguish "pure arb" vs "statistical price dislocation."
- Model: fees, transfer delays, withdrawal limits, inventory constraints.
- If true cross-exchange arb is infeasible, propose a realistic substitute:
  - Same-exchange triangular arb,
  - Order-book dislocation / microstructure mean reversion,
  - Basis/funding capture (perps),
  - Cross-asset pairs trading.

## 2) Risk-Aware System Thinking (Non-Negotiable)
Create a risk model that explicitly accounts for:
- Fees (maker/taker), spreads, slippage model, partial fills
- Liquidity constraints (max participation rate, min depth)
- Latency + stale signals
- Transfer delays (if multi-exchange), liquidation risk (if leverage)
- Exchange/broker outages, API bans, rate limits
- Tail events + circuit breakers

### 2.1 Realistic Profitability Assumptions
- Provide a sober expected performance range with caveats (e.g., after costs).
- List what must be true for profitability.
- List top reasons it will fail.

### 2.2 Position Sizing + Risk Limits
- Use volatility targeting (e.g., ATR/realized vol).
- Max drawdown guardrails, max leverage, max concentration, stop logic.
- Provide explicit formulas.

### 2.3 Robust Backtest Methodology
- Walk-forward splits, purging/embargo, transaction cost modeling.
- Avoid lookahead bias and survivorship bias.
- Monte Carlo / bootstrapping for robustness.
- Include a "kill switch criteria" list.

## 3) Full Product Architecture (Buildable, Production-Ready)
Design a modular architecture with:
- Data ingestion layer
- Feature store
- Signal generation engine (indicators + ML + sentiment + regime + arb scanner)
- Backtesting & simulation framework
- Risk management module
- Execution engine (broker/exchange adapters)
- Monitoring/alerting + dashboard
- Deployment & ops (containers, scheduling, secrets, logs, CI/CD)

### 3.1 Proposed Tech Stack (Justify Each)
Give a practical stack. Example categories:
- Python runtime + package mgmt
- Data: Postgres/TimescaleDB, Parquet/S3, Redis
- Streaming/queue: Kafka/Redpanda or Redis Streams (choose based on scope)
- Model training: scikit-learn, xgboost/lightgbm, PyTorch (only if needed)
- Backtesting: vectorized engine or custom event-driven (justify)
- APIs: FastAPI
- Observability: Prometheus/Grafana, OpenTelemetry, Sentry
- Infra: Docker, docker-compose, Terraform (optional), cloud provider
Be explicit about what runs where.

### 3.2 Module Tree (Required)
Output a repo structure like:
/README.md
/apps
  /api
  /worker
/packages
  /data_ingestion
  /features
  /models
  /signals
  /risk
  /execution
  /backtest
  /monitoring
  /common
Provide a 1-2 line description per module.

### 3.3 Data Schemas (Required)
Define tables/collections with key fields:
- candles / trades / orderbook snapshots
- features
- sentiment events
- model predictions
- signals
- orders / fills
- positions / PnL
- risk metrics
Include timestamps, symbol conventions, and idempotency keys.

### 3.4 API Contracts (Required)
Define key interfaces:
- MarketDataProvider
- SentimentProvider
- FeatureComputer
- ModelPredictor
- SignalCombiner
- RiskManager
- ExecutionAdapter (per exchange/broker)
- PortfolioStateStore
Provide method signatures (Python typing) and error handling strategy.

## 4) Key Algorithms + Pseudocode (Required)
Provide pseudocode for:
1) Ingestion loop (with retries, rate limits, backfill)
2) Feature pipeline (batch + streaming modes)
3) Training loop (walk-forward), model registry, and evaluation
4) Regime detector update + gating logic
5) Signal fusion (ensemble + confidence weighting)
6) Risk checks (pre-trade and post-trade)
7) Execution algorithm (limit/market decision, TWAP/VWAP if relevant, order monitoring)
8) Backtest engine loop (event-driven recommended if execution realism matters)

Also include:
- Slippage + fee model formulas
- A minimal example configuration file (YAML/JSON) controlling parameters

## 5) Backtesting & Simulation Framework (Deep + Practical)
- Choose event-driven vs vectorized and justify.
- Show how to simulate:
  - partial fills
  - latency
  - spread crossing
  - order cancellations
- Include benchmark comparisons:
  - Buy-and-hold
  - Simple MA crossover
  - Pure mean reversion baseline
- Provide evaluation metrics:
  - Sharpe/Sortino (with caveats), max drawdown, turnover, hit rate, tail loss
  - Capacity estimate (how much capital before edge decays)

## 6) Monitoring, Alerting, and Dashboard
- What to monitor: data freshness, model drift, regime flips, PnL attribution, execution quality, error budgets.
- Alert rules (thresholds, anomaly detection).
- A dashboard layout (pages + key charts).
- Incident runbook outline (what to do when X fails).

## 7) Deployment Architecture (Production)
- Environments: local, staging (paper), production (small capital).
- Containerization: Docker + compose; optional Kubernetes only if justified.
- Scheduling: cron, Celery, or temporal workflows.
- Secrets: vault approach, env vars, KMS.
- CI/CD: tests, lint, type checks, backtest regression tests.

## 8) MVP Roadmap (Step-by-Step)
Provide a staged plan with deliverables:
- Week 1: data + baseline backtest
- Week 2: ML baseline + walk-forward
- Week 3: regime gating + risk
- Week 4: paper trading + monitoring
- Week 5+: live small-capital + iteration
Each stage must list:
- success criteria
- what can go wrong
- what logs/metrics to validate

## 9) Scaling Into a Real Product / Startup
- Path to multi-asset, multi-exchange, multi-strategy.
- Model ops: registry, retraining triggers, feature versioning.
- Data moat opportunities (without pretending guaranteed edge).
- Team roles if hiring 1-5 people.
- Security posture (keys, least privilege, audit logs).

## 10) "Unique Differentiation" (Make It Non-Generic)
Propose ONE unique angle that is not the usual "LSTM + RSI."
Examples (choose ONE and fully justify):
- Regime-gated mixture-of-experts combining: (trend model) + (microstructure mean reversion) + (sentiment shock absorber)
- Cross-venue dislocation detector paired with inventory-aware execution
- Uncertainty-aware allocation with drawdown-conditional risk budgets
You must explain:
- Why it could outperform basic bots
- How it is tested (ablation plan)
- Why it is still buildable by a solo developer

## 11) Safety and Ethics Guardrails
- Avoid manipulative strategies.
- Rate-limit and source-credibility checks for sentiment.
- Hard "stop trading" conditions.
- Paper trading requirement before any live funds.

=========================================================
FINAL CHECKLIST (Before you finish)
=========================================================
- Did you clearly state assumptions and constraints?
- Did you provide concrete module structure + interfaces + schemas?
- Did you include pseudocode for all critical loops?
- Did you model costs and execution realism?
- Did you provide an MVP plan and a scaling plan?
- Did you include failure modes and kill switches?
