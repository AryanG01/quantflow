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

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


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


class NormalizationConfig(BaseModel):
    method: str = "rolling_zscore"
    window: int = 100
    shift: int = 1


class FeaturesConfig(BaseModel):
    technical: TechnicalFeaturesConfig = Field(default_factory=TechnicalFeaturesConfig)
    normalization: NormalizationConfig = Field(default_factory=NormalizationConfig)


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


class ModelConfig(BaseModel):
    type: str = "lightgbm_quantile"
    quantiles: list[float] = Field(default_factory=lambda: [0.1, 0.25, 0.5, 0.75, 0.9])
    walk_forward: WalkForwardConfig = Field(default_factory=WalkForwardConfig)
    labeling: LabelingConfig = Field(default_factory=LabelingConfig)


class RegimeConfig(BaseModel):
    model: str = "gaussian_hmm"
    n_states: int = 3
    features: list[str] = Field(default_factory=lambda: ["log_returns", "realized_vol"])
    retrain_interval_days: int = 7
    state_mapping: dict[str, int] = Field(
        default_factory=lambda: {"trending": 0, "mean_reverting": 1, "choppy": 2}
    )


class RegimeWeights(BaseModel):
    technical: float = 0.33
    ml: float = 0.34
    sentiment: float = 0.33


class SignalFusionConfig(BaseModel):
    method: str = "regime_gated_moe"
    regime_weights: dict[str, RegimeWeights] = Field(default_factory=dict)
    choppy_scale: float = 0.3


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


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load config from YAML file with environment variable resolution."""
    config_path = Path("config/default.yaml") if config_path is None else Path(config_path)

    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f)
        resolved = _resolve_config(raw)
        return AppConfig.model_validate(resolved)

    return AppConfig()
