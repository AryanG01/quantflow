"""FastAPI backend for the AI Trading System.

Serves portfolio data, signals, positions, regime state, and risk metrics
to the frontend dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Trading System API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response Models ──────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float


class SignalResponse(BaseModel):
    symbol: str
    direction: str
    strength: float
    confidence: float
    regime: str
    components: dict[str, float]
    timestamp: str


class PositionResponse(BaseModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PortfolioResponse(BaseModel):
    equity: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown_pct: float
    timestamp: str


class RiskMetricsResponse(BaseModel):
    current_drawdown_pct: float
    max_drawdown_pct: float
    portfolio_vol: float
    sharpe_ratio: float | None
    concentration_pct: float
    kill_switch_active: bool


class RegimeResponse(BaseModel):
    current: str
    confidence: float
    history: list[dict[str, Any]]


class BacktestSummary(BaseModel):
    strategy: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    hit_rate: float


class EquityCurvePoint(BaseModel):
    timestamp: str
    equity: float


# ── In-memory state (replaced by DB queries in production) ───

_start_time = datetime.now(timezone.utc)
_latest_signals: dict[str, SignalResponse] = {}
_positions: list[PositionResponse] = []
_portfolio: PortfolioResponse | None = None
_risk_metrics: RiskMetricsResponse | None = None
_regime: RegimeResponse | None = None
_equity_history: list[EquityCurvePoint] = []
_backtest_results: list[BacktestSummary] = []


# ── Routes ───────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    now = datetime.now(timezone.utc)
    return HealthResponse(
        status="ok",
        timestamp=now.isoformat(),
        version="0.1.0",
        uptime_seconds=(now - _start_time).total_seconds(),
    )


@app.get("/api/signals", response_model=list[SignalResponse])
async def get_signals() -> list[SignalResponse]:
    return list(_latest_signals.values())


@app.get("/api/signals/{symbol}", response_model=SignalResponse | None)
async def get_signal(symbol: str) -> SignalResponse | None:
    return _latest_signals.get(symbol)


@app.get("/api/portfolio", response_model=PortfolioResponse | None)
async def get_portfolio() -> PortfolioResponse | None:
    return _portfolio


@app.get("/api/positions", response_model=list[PositionResponse])
async def get_positions() -> list[PositionResponse]:
    return _positions


@app.get("/api/risk", response_model=RiskMetricsResponse | None)
async def get_risk() -> RiskMetricsResponse | None:
    return _risk_metrics


@app.get("/api/regime", response_model=RegimeResponse | None)
async def get_regime() -> RegimeResponse | None:
    return _regime


@app.get("/api/equity-history", response_model=list[EquityCurvePoint])
async def get_equity_history() -> list[EquityCurvePoint]:
    return _equity_history


@app.get("/api/backtest-results", response_model=list[BacktestSummary])
async def get_backtest_results() -> list[BacktestSummary]:
    return _backtest_results


# ── State update functions (called by worker) ───────────────


def update_signal(symbol: str, signal: SignalResponse) -> None:
    _latest_signals[symbol] = signal


def update_portfolio(portfolio: PortfolioResponse) -> None:
    global _portfolio
    _portfolio = portfolio


def update_positions(positions: list[PositionResponse]) -> None:
    global _positions
    _positions = positions


def update_risk(risk: RiskMetricsResponse) -> None:
    global _risk_metrics
    _risk_metrics = risk


def update_regime(regime: RegimeResponse) -> None:
    global _regime
    _regime = regime


def add_equity_point(point: EquityCurvePoint) -> None:
    _equity_history.append(point)


def set_backtest_results(results: list[BacktestSummary]) -> None:
    global _backtest_results
    _backtest_results = results
