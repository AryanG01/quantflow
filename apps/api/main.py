"""FastAPI backend for the AI Trading System.

Serves portfolio data, signals, positions, regime state, and risk metrics
to the frontend dashboard. Reads from TimescaleDB when available, falls
back to demo data otherwise.
"""

from __future__ import annotations

import random
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from packages.common.config import load_config
from packages.common.logging import get_logger

logger = get_logger(__name__)


# ── Database ─────────────────────────────────────────────────

_cfg = load_config()
_engine: sa.engine.Engine | None = None
_metadata = sa.MetaData()

# Table references
_candles = sa.Table(
    "candles",
    _metadata,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("exchange", sa.Text),
    sa.Column("symbol", sa.Text),
    sa.Column("timeframe", sa.Text),
    sa.Column("open", sa.Float),
    sa.Column("high", sa.Float),
    sa.Column("low", sa.Float),
    sa.Column("close", sa.Float),
    sa.Column("volume", sa.Float),
)

_signals_table = sa.Table(
    "signals",
    _metadata,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("symbol", sa.Text),
    sa.Column("direction", sa.Text),
    sa.Column("strength", sa.Float),
    sa.Column("confidence", sa.Float),
    sa.Column("regime", sa.Text),
    sa.Column("components", sa.JSON),
)

_positions_table = sa.Table(
    "positions",
    _metadata,
    sa.Column("symbol", sa.Text),
    sa.Column("exchange", sa.Text),
    sa.Column("side", sa.Text),
    sa.Column("quantity", sa.Float),
    sa.Column("avg_entry_price", sa.Float),
    sa.Column("unrealized_pnl", sa.Float),
    sa.Column("realized_pnl", sa.Float),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)

_portfolio_table = sa.Table(
    "portfolio_snapshots",
    _metadata,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("equity", sa.Float),
    sa.Column("cash", sa.Float),
    sa.Column("positions_value", sa.Float),
    sa.Column("unrealized_pnl", sa.Float),
    sa.Column("realized_pnl", sa.Float),
    sa.Column("drawdown_pct", sa.Float),
)

_risk_table = sa.Table(
    "risk_metrics",
    _metadata,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("max_drawdown_pct", sa.Float),
    sa.Column("current_drawdown_pct", sa.Float),
    sa.Column("portfolio_vol", sa.Float),
    sa.Column("sharpe_ratio", sa.Float),
    sa.Column("concentration_pct", sa.Float),
    sa.Column("kill_switch_active", sa.Boolean),
)

_orders_table = sa.Table(
    "orders",
    _metadata,
    sa.Column("id", sa.Text),
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("symbol", sa.Text),
    sa.Column("exchange", sa.Text),
    sa.Column("side", sa.Text),
    sa.Column("order_type", sa.Text),
    sa.Column("quantity", sa.Float),
    sa.Column("price", sa.Float),
    sa.Column("status", sa.Text),
    sa.Column("filled_qty", sa.Float),
    sa.Column("avg_fill_price", sa.Float),
    sa.Column("fees", sa.Float),
    sa.Column("signal_id", sa.Text),
)


def _get_db() -> sa.engine.Engine | None:
    """Get database engine, creating it if needed."""
    global _engine
    if _engine is None:
        try:
            _engine = sa.create_engine(_cfg.database.url, pool_pre_ping=True)
            # Test connection
            with _engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            logger.info(
                "database_connected", url=_cfg.database.url.replace(_cfg.database.password, "***")
            )
        except Exception as e:
            logger.warning("database_unavailable", error=str(e))
            _engine = None
    return _engine


def _db_query(query: sa.Select) -> list[sa.Row] | None:
    """Execute a DB query, returning None if DB is unavailable."""
    engine = _get_db()
    if engine is None:
        return None
    try:
        with engine.connect() as conn:
            return list(conn.execute(query))
    except Exception as e:
        logger.warning("db_query_failed", error=str(e))
        return None


# ── Response Models ──────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    db_connected: bool
    candle_count: int


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


class TradeResponse(BaseModel):
    id: str
    timestamp: str
    symbol: str
    side: str
    quantity: float
    price: float
    fees: float
    pnl: float
    signal_strength: float
    regime: str


class CandleResponse(BaseModel):
    time: str
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class ConfigResponse(BaseModel):
    universe: dict[str, Any]
    risk: dict[str, Any]
    execution: dict[str, Any]
    features: dict[str, Any]
    model: dict[str, Any]
    regime: dict[str, Any]


# ── Demo data fallback ───────────────────────────────────────

_start_time = datetime.now(UTC)


def _generate_demo_data() -> dict[str, Any]:
    """Generate realistic demo data for the dashboard when DB is empty."""
    now = datetime.now(UTC)
    random.seed(42)

    # Equity curve: 90 days
    equity_history = []
    equity = 100_000.0
    for i in range(90 * 6):
        daily_return = random.gauss(0.0003, 0.012)
        equity *= 1 + daily_return
        ts = now - timedelta(hours=(90 * 6 - i) * 4)
        equity_history.append(EquityCurvePoint(timestamp=ts.isoformat(), equity=round(equity, 2)))

    current_equity = equity_history[-1].equity
    peak_equity = max(p.equity for p in equity_history)
    drawdown = (peak_equity - current_equity) / peak_equity

    signals = [
        SignalResponse(
            symbol="BTC/USDT",
            direction="long",
            strength=0.72,
            confidence=0.85,
            regime="trending",
            components={"technical": 0.65, "ml": 0.80, "sentiment": 0.15},
            timestamp=now.isoformat(),
        ),
        SignalResponse(
            symbol="ETH/USDT",
            direction="short",
            strength=-0.35,
            confidence=0.62,
            regime="mean_reverting",
            components={"technical": -0.40, "ml": -0.25, "sentiment": -0.10},
            timestamp=(now - timedelta(hours=1)).isoformat(),
        ),
        SignalResponse(
            symbol="SOL/USDT",
            direction="flat",
            strength=0.08,
            confidence=0.41,
            regime="choppy",
            components={"technical": 0.12, "ml": -0.05, "sentiment": 0.10},
            timestamp=(now - timedelta(hours=2)).isoformat(),
        ),
    ]

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

    trades = []
    trade_symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    for i in range(50):
        sym = trade_symbols[i % 3]
        side = "buy" if i % 2 == 0 else "sell"
        price = {
            "BTC/USDT": 95_000 + random.uniform(-3000, 3000),
            "ETH/USDT": 3_400 + random.uniform(-200, 200),
            "SOL/USDT": 180 + random.uniform(-20, 20),
        }[sym]
        qty = {
            "BTC/USDT": round(random.uniform(0.01, 0.5), 4),
            "ETH/USDT": round(random.uniform(0.5, 5), 3),
            "SOL/USDT": round(random.uniform(5, 50), 2),
        }[sym]
        trades.append(
            TradeResponse(
                id=f"T{1000 + i}",
                timestamp=(now - timedelta(hours=i * 4 + random.randint(0, 3))).isoformat(),
                symbol=sym,
                side=side,
                quantity=qty,
                price=round(price, 2),
                fees=round(price * qty * 0.001, 2),
                pnl=round(random.uniform(-500, 800), 2),
                signal_strength=round(random.uniform(-1, 1), 3),
                regime=["trending", "mean_reverting", "choppy"][i % 3],
            )
        )

    backtest_results = [
        BacktestSummary(
            strategy="Full System (Regime-Gated MoE)",
            total_return=0.342,
            sharpe_ratio=1.85,
            max_drawdown=0.087,
            total_trades=156,
            hit_rate=0.58,
        ),
        BacktestSummary(
            strategy="Buy & Hold",
            total_return=0.215,
            sharpe_ratio=0.92,
            max_drawdown=0.234,
            total_trades=1,
            hit_rate=1.0,
        ),
        BacktestSummary(
            strategy="MA Crossover (20/50)",
            total_return=0.178,
            sharpe_ratio=1.12,
            max_drawdown=0.156,
            total_trades=42,
            hit_rate=0.52,
        ),
        BacktestSummary(
            strategy="No Regime (equal weights)",
            total_return=0.256,
            sharpe_ratio=1.41,
            max_drawdown=0.121,
            total_trades=148,
            hit_rate=0.54,
        ),
        BacktestSummary(
            strategy="No Sentiment",
            total_return=0.318,
            sharpe_ratio=1.72,
            max_drawdown=0.092,
            total_trades=152,
            hit_rate=0.57,
        ),
    ]

    return {
        "signals": signals,
        "positions": positions,
        "portfolio": portfolio,
        "risk": risk,
        "regime": regime,
        "equity_history": equity_history,
        "trades": trades,
        "backtest_results": backtest_results,
    }


_demo = _generate_demo_data()


# ── DB query helpers ─────────────────────────────────────────


def _get_latest_prices() -> dict[str, float]:
    """Get latest close price per symbol from candles."""
    query = (
        sa.select(_candles.c.symbol, _candles.c.close)
        .distinct(_candles.c.symbol)
        .order_by(_candles.c.symbol, _candles.c.time.desc())
    )
    rows = _db_query(query)
    if not rows:
        return {}
    return {row.symbol: row.close for row in rows}


def _get_candle_count() -> int:
    """Get total candle count."""
    query = sa.select(sa.func.count()).select_from(_candles)
    rows = _db_query(query)
    if not rows:
        return 0
    return rows[0][0]


def _get_db_signals() -> list[SignalResponse] | None:
    """Get latest signal per symbol from DB."""
    query = (
        sa.select(_signals_table)
        .distinct(_signals_table.c.symbol)
        .order_by(_signals_table.c.symbol, _signals_table.c.time.desc())
    )
    rows = _db_query(query)
    if not rows:
        return None
    return [
        SignalResponse(
            symbol=r.symbol,
            direction=r.direction,
            strength=r.strength,
            confidence=r.confidence,
            regime=r.regime,
            components=r.components if r.components else {},
            timestamp=r.time.isoformat(),
        )
        for r in rows
    ]


def _get_db_positions() -> list[PositionResponse] | None:
    """Get positions from DB, enriched with latest prices."""
    query = sa.select(_positions_table).where(_positions_table.c.quantity > 0)
    rows = _db_query(query)
    if not rows:
        return None
    prices = _get_latest_prices()
    result = []
    for r in rows:
        current = prices.get(r.symbol, r.avg_entry_price or 0)
        entry = r.avg_entry_price or current
        pnl = (current - entry) * r.quantity if r.side == "long" else (entry - current) * r.quantity
        pnl_pct = (pnl / (entry * r.quantity) * 100) if entry * r.quantity > 0 else 0
        result.append(
            PositionResponse(
                symbol=r.symbol,
                side=r.side,
                quantity=r.quantity,
                entry_price=entry,
                current_price=current,
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 2),
            )
        )
    return result


def _get_db_portfolio() -> PortfolioResponse | None:
    """Get latest portfolio snapshot from DB."""
    query = sa.select(_portfolio_table).order_by(_portfolio_table.c.time.desc()).limit(1)
    rows = _db_query(query)
    if not rows:
        return None
    r = rows[0]
    return PortfolioResponse(
        equity=r.equity,
        cash=r.cash,
        positions_value=r.positions_value,
        unrealized_pnl=r.unrealized_pnl,
        realized_pnl=r.realized_pnl,
        drawdown_pct=r.drawdown_pct,
        timestamp=r.time.isoformat(),
    )


def _get_db_risk() -> RiskMetricsResponse | None:
    """Get latest risk metrics from DB."""
    query = sa.select(_risk_table).order_by(_risk_table.c.time.desc()).limit(1)
    rows = _db_query(query)
    if not rows:
        return None
    r = rows[0]
    return RiskMetricsResponse(
        current_drawdown_pct=r.current_drawdown_pct,
        max_drawdown_pct=r.max_drawdown_pct,
        portfolio_vol=r.portfolio_vol,
        sharpe_ratio=r.sharpe_ratio,
        concentration_pct=r.concentration_pct,
        kill_switch_active=r.kill_switch_active,
    )


def _get_db_equity_history() -> list[EquityCurvePoint] | None:
    """Get equity curve from portfolio snapshots."""
    query = sa.select(_portfolio_table.c.time, _portfolio_table.c.equity).order_by(
        _portfolio_table.c.time
    )
    rows = _db_query(query)
    if not rows:
        return None
    return [EquityCurvePoint(timestamp=r.time.isoformat(), equity=r.equity) for r in rows]


def _get_db_trades() -> list[TradeResponse] | None:
    """Get filled orders as trades from DB."""
    query = (
        sa.select(_orders_table)
        .where(_orders_table.c.status == "filled")
        .order_by(_orders_table.c.time.desc())
        .limit(200)
    )
    rows = _db_query(query)
    if not rows:
        return None
    return [
        TradeResponse(
            id=r.id,
            timestamp=r.time.isoformat(),
            symbol=r.symbol,
            side=r.side,
            quantity=r.filled_qty or r.quantity,
            price=r.avg_fill_price or r.price or 0,
            fees=r.fees or 0,
            pnl=0,
            signal_strength=0,
            regime="unknown",
        )
        for r in rows
    ]


# ── App lifecycle ────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Initialize DB connection on startup."""
    _get_db()
    yield
    if _engine:
        _engine.dispose()


app = FastAPI(title="AI Trading System API", version="0.1.0", lifespan=lifespan)

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


# ── Routes ───────────────────────────────────────────────────


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    now = datetime.now(UTC)
    db_ok = _get_db() is not None
    return HealthResponse(
        status="ok",
        timestamp=now.isoformat(),
        version="0.1.0",
        uptime_seconds=(now - _start_time).total_seconds(),
        db_connected=db_ok,
        candle_count=_get_candle_count() if db_ok else 0,
    )


@app.get("/api/signals", response_model=list[SignalResponse])
async def get_signals() -> list[SignalResponse]:
    db_signals = _get_db_signals()
    return db_signals if db_signals else _demo["signals"]


@app.get("/api/signals/{symbol}", response_model=SignalResponse | None)
async def get_signal(symbol: str) -> SignalResponse | None:
    db_signals = _get_db_signals()
    if db_signals:
        return next((s for s in db_signals if s.symbol == symbol), None)
    return next((s for s in _demo["signals"] if s.symbol == symbol), None)


@app.get("/api/portfolio", response_model=PortfolioResponse | None)
async def get_portfolio() -> PortfolioResponse | None:
    return _get_db_portfolio() or _demo["portfolio"]


@app.get("/api/positions", response_model=list[PositionResponse])
async def get_positions() -> list[PositionResponse]:
    return _get_db_positions() or _demo["positions"]


@app.get("/api/risk", response_model=RiskMetricsResponse | None)
async def get_risk() -> RiskMetricsResponse | None:
    return _get_db_risk() or _demo["risk"]


@app.get("/api/regime", response_model=RegimeResponse | None)
async def get_regime() -> RegimeResponse | None:
    # No dedicated regime table — derive from signals
    db_signals = _get_db_signals()
    if db_signals:
        current = db_signals[0]
        return RegimeResponse(
            current=current.regime,
            confidence=current.confidence,
            history=[{"timestamp": s.timestamp, "regime": s.regime} for s in db_signals],
        )
    return _demo["regime"]


@app.get("/api/equity-history", response_model=list[EquityCurvePoint])
async def get_equity_history() -> list[EquityCurvePoint]:
    return _get_db_equity_history() or _demo["equity_history"]


@app.get("/api/backtest-results", response_model=list[BacktestSummary])
async def get_backtest_results() -> list[BacktestSummary]:
    # Backtest results are not stored in DB — always from demo/cache
    return _demo["backtest_results"]


@app.get("/api/trades", response_model=list[TradeResponse])
async def get_trades() -> list[TradeResponse]:
    return _get_db_trades() or _demo["trades"]


@app.get("/api/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    return ConfigResponse(
        universe=_cfg.universe.model_dump(),
        risk=_cfg.risk.model_dump(),
        execution=_cfg.execution.model_dump(),
        features=_cfg.features.model_dump(),
        model=_cfg.model.model_dump(),
        regime=_cfg.regime.model_dump(),
    )


@app.get("/api/candles/{symbol:path}", response_model=list[CandleResponse])
async def get_candles(symbol: str, limit: int = 500) -> list[CandleResponse]:
    """Get recent candles for a symbol from the database."""
    query = (
        sa.select(_candles)
        .where(_candles.c.symbol == symbol)
        .order_by(_candles.c.time.desc())
        .limit(limit)
    )
    rows = _db_query(query)
    if not rows:
        return []
    return [
        CandleResponse(
            time=r.time.isoformat(),
            symbol=r.symbol,
            open=r.open,
            high=r.high,
            low=r.low,
            close=r.close,
            volume=r.volume,
        )
        for r in reversed(rows)  # return oldest first
    ]


@app.get("/api/prices", response_model=dict[str, float])
async def get_prices() -> dict[str, float]:
    """Get latest prices for all symbols."""
    return _get_latest_prices()
