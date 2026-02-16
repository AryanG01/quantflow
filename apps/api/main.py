"""FastAPI backend for the AI Trading System.

Serves portfolio data, signals, positions, regime state, and risk metrics
to the frontend dashboard.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Trading System API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:4000",
    ],
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

_start_time = datetime.now(UTC)


def _generate_demo_data() -> dict[str, Any]:
    """Generate realistic demo data for the dashboard."""
    now = datetime.now(UTC)

    # Equity curve: 90 days of simulated growth with noise
    equity_history = []
    equity = 100_000.0
    random.seed(42)
    for i in range(90 * 6):  # 6 bars per day (4h bars)
        daily_return = random.gauss(0.0003, 0.012)
        equity *= 1 + daily_return
        ts = now - timedelta(hours=(90 * 6 - i) * 4)
        equity_history.append(EquityCurvePoint(timestamp=ts.isoformat(), equity=round(equity, 2)))

    current_equity = equity_history[-1].equity
    peak_equity = max(p.equity for p in equity_history)
    drawdown = (peak_equity - current_equity) / peak_equity

    # Signals
    signals = {
        "BTC/USDT": SignalResponse(
            symbol="BTC/USDT",
            direction="long",
            strength=0.72,
            confidence=0.85,
            regime="trending",
            components={"technical": 0.65, "ml": 0.80, "sentiment": 0.15},
            timestamp=now.isoformat(),
        ),
        "ETH/USDT": SignalResponse(
            symbol="ETH/USDT",
            direction="short",
            strength=-0.35,
            confidence=0.62,
            regime="mean_reverting",
            components={"technical": -0.40, "ml": -0.25, "sentiment": -0.10},
            timestamp=(now - timedelta(hours=1)).isoformat(),
        ),
        "SOL/USDT": SignalResponse(
            symbol="SOL/USDT",
            direction="flat",
            strength=0.08,
            confidence=0.41,
            regime="choppy",
            components={"technical": 0.12, "ml": -0.05, "sentiment": 0.10},
            timestamp=(now - timedelta(hours=2)).isoformat(),
        ),
    }

    # Positions
    positions = [
        PositionResponse(
            symbol="BTC/USDT",
            side="long",
            quantity=0.45,
            entry_price=96_420.0,
            current_price=98_150.0,
            unrealized_pnl=778.50,
            unrealized_pnl_pct=1.79,
        ),
        PositionResponse(
            symbol="ETH/USDT",
            side="short",
            quantity=3.2,
            entry_price=3_450.0,
            current_price=3_380.0,
            unrealized_pnl=224.0,
            unrealized_pnl_pct=2.03,
        ),
    ]

    positions_value = sum(p.quantity * p.current_price for p in positions)
    unrealized_pnl = sum(p.unrealized_pnl for p in positions)
    cash = current_equity - positions_value

    portfolio = PortfolioResponse(
        equity=round(current_equity, 2),
        cash=round(cash, 2),
        positions_value=round(positions_value, 2),
        unrealized_pnl=round(unrealized_pnl, 2),
        realized_pnl=4_325.80,
        drawdown_pct=round(drawdown, 4),
        timestamp=now.isoformat(),
    )

    risk = RiskMetricsResponse(
        current_drawdown_pct=round(drawdown, 4),
        max_drawdown_pct=round(drawdown + 0.02, 4),
        portfolio_vol=0.142,
        sharpe_ratio=1.85,
        concentration_pct=round(positions_value / current_equity, 4) if current_equity > 0 else 0,
        kill_switch_active=False,
    )

    regime = RegimeResponse(
        current="trending",
        confidence=0.85,
        history=[
            {"timestamp": (now - timedelta(hours=h * 4)).isoformat(), "regime": r}
            for h, r in [
                (0, "trending"),
                (1, "trending"),
                (2, "mean_reverting"),
                (3, "mean_reverting"),
                (4, "choppy"),
                (5, "trending"),
            ]
        ],
    )

    return {
        "signals": signals,
        "positions": positions,
        "portfolio": portfolio,
        "risk": risk,
        "regime": regime,
        "equity_history": equity_history,
    }


# Generate demo data on startup
_demo = _generate_demo_data()
_latest_signals: dict[str, SignalResponse] = _demo["signals"]
_positions: list[PositionResponse] = _demo["positions"]
_portfolio: PortfolioResponse | None = _demo["portfolio"]
_risk_metrics: RiskMetricsResponse | None = _demo["risk"]
_regime: RegimeResponse | None = _demo["regime"]
_equity_history: list[EquityCurvePoint] = _demo["equity_history"]
_backtest_results: list[BacktestSummary] = []


# ── Routes ───────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    now = datetime.now(UTC)
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
