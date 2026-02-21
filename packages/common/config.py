"""Configuration loading from YAML + environment variables."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


def _resolve_env_vars(value: str) -> str:
    """Resolve ${VAR:default} patterns in strings."""
    pattern = r"\$\{(\w+)(?::([^}]*))?\}"

    def replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default = match.group(2)
        return os.environ.get(var_name, default if default is not None else "")

    return re.sub(pattern, replacer, value)


def _resolve_config(obj: Any) -> Any:
    """Recursively resolve environment variables in config."""
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _resolve_config(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_config(v) for v in obj]
    return obj


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    name: str = "trading"
    user: str = "trading"
    password: str = "changeme"
    sslmode: str = ""  # e.g. "require" for Timescale Cloud

    @property
    def url(self) -> str:
        base = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        if self.sslmode:
            return f"{base}?sslmode={self.sslmode}"
        return base


class RedisConfig(BaseModel):
    url: str = "redis://localhost:6379/0"


class UniverseConfig(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["BTC/USDT"])
    timeframe: str = "4h"
    lookback_days: int = 730


class TechnicalFeaturesConfig(BaseModel):
    rsi_period: int = 14
    atr_period: int = 14
    bb_period: int = 20
    bb_std: float = 2.0
    vol_window: int = 24
    vwap_period: int = 24
    bars_per_year: int = 2190  # 6 bars/day × 365 days (4h timeframe)


class NormalizationConfig(BaseModel):
    method: str = "rolling_zscore"
    window: int = 100
    shift: int = 1


class FeaturesConfig(BaseModel):
    technical: TechnicalFeaturesConfig = Field(default_factory=TechnicalFeaturesConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)
    use_orderbook: bool = False  # set True only when live orderbook snapshots are available


class WalkForwardConfig(BaseModel):
    train_bars: int = 1000
    test_bars: int = 100
    purge_bars: int = 3
    embargo_bars: int = 2


class LabelingConfig(BaseModel):
    method: str = "triple_barrier"
    profit_taking_pct: float = 0.03
    stop_loss_pct: float = 0.015
    max_holding_bars: int = 12
    neutral_pct: float = 0.005  # return threshold for neutral label at time barrier


class ModelConfig(BaseModel):
    type: str = "lightgbm_quantile"
    n_estimators: int = 200
    learning_rate: float = 0.05
    max_depth: int = 6
    num_leaves: int = 31
    quantiles: list[float] = Field(default_factory=lambda: [0.1, 0.25, 0.5, 0.75, 0.9])
    walk_forward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    labeling: LabelingConfig = Field(default_factory=LabelingConfig)


class RegimeConfig(BaseModel):
    model: str = "gaussian_hmm"
    n_states: int = 3
    features: list[str] = Field(default_factory=lambda: ["log_returns", "realized_vol"])
    retrain_interval_days: int = 7


class RegimeWeights(BaseModel):
    technical: float = 0.33
    ml: float = 0.34
    sentiment: float = 0.33


class SignalFusionConfig(BaseModel):
    method: str = "regime_gated_moe"
    regime_weights: dict[str, RegimeWeights] = Field(
        default_factory=lambda: {
            "trending": RegimeWeights(technical=0.4, ml=0.5, sentiment=0.1),
            "mean_reverting": RegimeWeights(technical=0.5, ml=0.3, sentiment=0.2),
            "choppy": RegimeWeights(technical=0.3, ml=0.3, sentiment=0.4),
        }
    )
    choppy_scale: float = 0.3
    direction_threshold: float = 0.05  # |strength| above this → directional signal
    confidence_min_iqr: float = 0.2  # IQR at which model confidence → 1.0
    confidence_max_iqr: float = 1.5  # IQR at which model confidence → 0.0


class SignalsConfig(BaseModel):
    fusion: SignalFusionConfig = Field(default_factory=SignalFusionConfig)


class RiskConfig(BaseModel):
    vol_target: float = 0.15
    max_position_pct: float = 0.25
    max_portfolio_leverage: float = 1.0
    max_drawdown_pct: float = 0.15
    max_concentration_pct: float = 0.30
    min_trade_usd: float = 10.0
    staleness_threshold_minutes: int = 30


class SlippageModelConfig(BaseModel):
    fixed_spread_bps: float = 5.0
    linear_impact_bps: float = 2.0


class ExecutionConfig(BaseModel):
    mode: str = "paper"
    order_timeout_seconds: int = 120
    max_retries: int = 3
    slippage_model: SlippageModelConfig = Field(default_factory=SlippageModelConfig)


class ExchangeFees(BaseModel):
    maker: float = 10.0
    taker: float = 10.0


class ExchangeConfig(BaseModel):
    sandbox: bool = True
    rate_limit_rpm: int = 1200
    fees_bps: ExchangeFees = Field(default_factory=ExchangeFees)


class MonitoringConfig(BaseModel):
    prometheus_port: int = 9090
    alert_webhook_url: str = ""
    drift_psi_threshold: float = 0.2
    telegram_bot_token: str = ""  # set via env var TELEGRAM_BOT_TOKEN
    telegram_chat_id: str = ""  # set via env var TELEGRAM_CHAT_ID


class WorkerConfig(BaseModel):
    signal_interval_hours: int = 4
    candle_interval_hours: int = 1
    sentiment_interval_minutes: int = 5
    health_interval_seconds: int = 60
    loop_sleep_seconds: int = 10
    candle_backfill_hours: int = 2
    sentiment_retention_hours: int = 24


class PortfolioConfig(BaseModel):
    initial_equity: float = 100_000.0
    signal_lookback_bars: int = 1200  # 4h bars ≈ 200 days
    min_train_bars: int = 500
    min_valid_labels: int = 200
    vol_lookback_bars: int = 90  # bars used for vol/Sharpe estimation


class ApiConfig(BaseModel):
    version: str = "0.1.0"
    # CORS origins can be overridden via CORS_ORIGINS env var (comma-separated)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:4000",
        ]
    )


class SentimentConfig(BaseModel):
    decay_halflife_hours: float = 12.0
    max_events_per_source: int = 10
    staleness_hours: float = 24.0
    dedup_window_hours: float = 6.0


class AppConfig(BaseModel):
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    regime: RegimeConfig = Field(default_factory=RegimeConfig)
    signals: SignalsConfig = Field(default_factory=SignalsConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    exchanges: dict[str, ExchangeConfig] = Field(default_factory=dict)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    worker: WorkerConfig = Field(default_factory=WorkerConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    sentiment: SentimentConfig = Field(default_factory=SentimentConfig)


def save_config(config: AppConfig, config_path: str | Path | None = None) -> None:
    """Save config to YAML file, preserving env-var placeholders for DB/Redis."""
    config_path = Path("config/default.yaml") if config_path is None else Path(config_path)

    # Read existing raw YAML to preserve env-var patterns
    existing_raw: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path) as f:
            existing_raw = yaml.safe_load(f) or {}

    dumped = config.model_dump()

    # Preserve database/redis sections from original file (they use ${VAR:default})
    for key in ("database", "redis"):
        if key in existing_raw:
            dumped[key] = existing_raw[key]

    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(dumped, f, default_flow_style=False, sort_keys=False)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load config from YAML file with environment variable resolution."""
    config_path = Path("config/default.yaml") if config_path is None else Path(config_path)

    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        resolved = _resolve_config(raw)
        return AppConfig.model_validate(resolved)

    return AppConfig()
