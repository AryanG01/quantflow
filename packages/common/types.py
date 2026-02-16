"""Domain types for the AI Trading System."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Regime(str, Enum):
    TRENDING = "trending"
    MEAN_REVERTING = "mean_reverting"
    CHOPPY = "choppy"


class Candle(BaseModel):
    time: datetime
    exchange: str
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class Signal(BaseModel):
    time: datetime
    symbol: str
    direction: Direction
    strength: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    regime: Regime
    components: dict[str, float] = Field(default_factory=dict)


class Order(BaseModel):
    id: str
    time: datetime
    symbol: str
    exchange: str
    side: Side
    order_type: OrderType
    quantity: float
    price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: float | None = None
    fees: float = 0.0
    signal_id: str | None = None


class Position(BaseModel):
    symbol: str
    exchange: str
    side: Direction
    quantity: float = 0.0
    avg_entry_price: float | None = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class PortfolioSnapshot(BaseModel):
    time: datetime
    equity: float
    cash: float
    positions_value: float
    unrealized_pnl: float
    realized_pnl: float
    drawdown_pct: float


class PredictionResult(BaseModel):
    time: datetime
    symbol: str
    model_id: str
    quantiles: dict[str, float]  # {"q10": 0.01, "q25": 0.005, ...}
    label: int  # 0=down, 1=neutral, 2=up
    confidence: float = Field(ge=0.0, le=1.0)
