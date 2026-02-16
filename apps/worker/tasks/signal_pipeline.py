"""End-to-end signal generation pipeline.

Runs every 4h: candles → features → predict → regime → fuse → risk → size → execute.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pandas as pd
import sqlalchemy as sa

from packages.common.logging import get_logger
from packages.common.types import Direction, OrderType, PortfolioSnapshot, Side
from packages.execution.order_manager import OrderManager
from packages.features.normalizer import RollingZScoreNormalizer
from packages.features.technical import TechnicalFeatures
from packages.models.labeling import triple_barrier_labels
from packages.models.lightgbm_model import LightGBMQuantileModel
from packages.monitoring.metrics_exporter import (
    record_error,
    record_order,
    record_rejection,
    signal_strength_gauge,
    update_portfolio_metrics,
)
from packages.risk.drawdown_monitor import DrawdownMonitor
from packages.risk.position_sizer import VolTargetPositionSizer
from packages.risk.risk_checks import RiskChecker
from packages.signals.confidence import uncertainty_to_confidence
from packages.signals.regime_detector import RegimeDetector
from packages.signals.signal_fusion import RegimeGatedMoE

if TYPE_CHECKING:
    from packages.common.config import AppConfig

logger = get_logger(__name__)


class SignalPipeline:
    """Orchestrates the full signal generation and execution pipeline."""

    def __init__(self, config: AppConfig, engine: sa.engine.Engine) -> None:
        self._config = config
        self._engine = engine

        # Feature computation
        tech_cfg = config.features.technical
        self._feature_computer = TechnicalFeatures(
            rsi_period=tech_cfg.rsi_period,
            atr_period=tech_cfg.atr_period,
            bb_period=tech_cfg.bb_period,
            bb_std=tech_cfg.bb_std,
            vol_window=tech_cfg.vol_window,
            vwap_period=tech_cfg.vwap_period,
        )
        norm_cfg = config.features.normalization
        self._normalizer = RollingZScoreNormalizer(
            window=norm_cfg.window, shift=norm_cfg.shift
        )

        # ML model (retrained periodically, loaded from registry in production)
        self._model = LightGBMQuantileModel(quantiles=config.model.quantiles)
        self._model_trained = False

        # Regime detection
        self._regime_detector = RegimeDetector(n_states=config.regime.n_states)
        self._regime_fitted = False

        # Signal fusion
        self._fusioner = RegimeGatedMoE(config.signals.fusion)

        # Risk
        self._risk_checker = RiskChecker(
            max_drawdown_pct=config.risk.max_drawdown_pct,
            max_concentration_pct=config.risk.max_concentration_pct,
            max_position_pct=config.risk.max_position_pct,
            min_trade_usd=config.risk.min_trade_usd,
            staleness_threshold_minutes=config.risk.staleness_threshold_minutes,
        )
        self._position_sizer = VolTargetPositionSizer(
            vol_target=config.risk.vol_target,
            max_position_pct=config.risk.max_position_pct,
        )
        self._drawdown_monitor = DrawdownMonitor(
            max_drawdown_pct=config.risk.max_drawdown_pct
        )

        # Execution
        self._order_manager = OrderManager(
            paper_mode=(config.execution.mode == "paper")
        )

        # Portfolio state (simplified in-memory for now)
        self._equity = 100_000.0
        self._cash = 100_000.0
        self._positions_value = 0.0

    def _fetch_candles(self, symbol: str, lookback_bars: int = 1200) -> pd.DataFrame:
        """Fetch recent candles from the database."""
        query = sa.text(
            """
            SELECT time, open, high, low, close, volume
            FROM candles
            WHERE symbol = :symbol AND timeframe = :timeframe
            ORDER BY time DESC
            LIMIT :limit
            """
        )
        with self._engine.connect() as conn:
            result = conn.execute(
                query,
                {"symbol": symbol, "timeframe": self._config.universe.timeframe, "limit": lookback_bars},
            )
            rows = result.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
        return df.sort_values("time").reset_index(drop=True)

    def _train_if_needed(self, candles: pd.DataFrame) -> None:
        """Train model and regime detector if not yet trained."""
        if self._model_trained and self._regime_fitted:
            return

        features = self._feature_computer.compute(candles)
        normalized = self._normalizer.normalize(features)

        # Drop NaN rows from warmup
        valid_mask = normalized.notna().all(axis=1)
        clean_features = normalized[valid_mask]
        clean_candles = candles[valid_mask]

        if len(clean_features) < 500:
            logger.warning("insufficient_data_for_training", n=len(clean_features))
            return

        # Train regime detector
        if not self._regime_fitted:
            log_ret = features["log_returns"].values[valid_mask]
            real_vol = features["realized_vol"].values[valid_mask]
            self._regime_detector.fit(log_ret, real_vol)
            self._regime_fitted = True

        # Train ML model
        if not self._model_trained:
            labels = triple_barrier_labels(
                clean_candles["close"],
                profit_taking_pct=self._config.model.labeling.profit_taking_pct,
                stop_loss_pct=self._config.model.labeling.stop_loss_pct,
                max_holding_bars=self._config.model.labeling.max_holding_bars,
            )
            valid_labels = labels >= 0
            if valid_labels.sum() > 200:
                self._model.train(
                    clean_features[valid_labels],
                    labels[valid_labels],
                )
                self._model_trained = True
                logger.info("model_trained", n_samples=int(valid_labels.sum()))

    async def run_for_symbol(self, symbol: str) -> None:
        """Run the full pipeline for a single symbol."""
        try:
            # 1. Fetch candles
            candles = self._fetch_candles(symbol)
            if candles.empty:
                logger.warning("no_candles", symbol=symbol)
                return

            # 2. Train models if needed
            self._train_if_needed(candles)

            # 3. Compute features
            features = self._feature_computer.compute(candles)
            normalized = self._normalizer.normalize(features)

            # Get last valid row for prediction
            last_valid = normalized.dropna().iloc[-1:]
            if last_valid.empty:
                return

            # 4. Predict
            if self._model_trained:
                predictions = self._model.predict(last_valid)
                pred = predictions[0]
                iqr = pred.quantiles.get("q75", 1.0) - pred.quantiles.get("q25", 0.0)
                confidence = uncertainty_to_confidence(iqr)
                ml_score = (pred.label - 1) / 1.0  # map 0,1,2 → -1,0,1
            else:
                confidence = 0.3
                ml_score = 0.0

            # 5. Detect regime
            log_ret = features["log_returns"].dropna().values
            real_vol = features["realized_vol"].dropna().values
            regime = self._regime_detector.predict_current(log_ret, real_vol)

            # 6. Technical signal (simple: RSI-based)
            rsi = features["rsi"].iloc[-1]
            tech_score = (50 - rsi) / 50 if pd.notna(rsi) else 0.0

            # 7. Fuse signals
            components = {
                "technical": tech_score,
                "ml": ml_score,
                "sentiment": 0.0,  # placeholder until sentiment is wired
            }
            signal = self._fusioner.combine(components, regime, confidence, symbol)

            signal_strength_gauge.labels(symbol=symbol).set(signal.strength)
            logger.info(
                "signal_generated",
                symbol=symbol,
                direction=signal.direction.value,
                strength=round(signal.strength, 4),
                confidence=round(signal.confidence, 4),
                regime=regime.value,
            )

            # 8. Risk check
            current_price = float(candles["close"].iloc[-1])
            portfolio = PortfolioSnapshot(
                time=datetime.now(UTC),
                equity=self._equity,
                cash=self._cash,
                positions_value=self._positions_value,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                drawdown_pct=self._drawdown_monitor.current_drawdown,
            )

            # 9. Position sizing
            realized_vol = float(features["realized_vol"].iloc[-1]) if pd.notna(features["realized_vol"].iloc[-1]) else 0.3
            quantity = self._position_sizer.compute_size(
                signal, portfolio, current_price, realized_vol
            )

            if quantity < 1e-8 or signal.direction == Direction.FLAT:
                return

            trade_value = quantity * current_price
            approved, reason = self._risk_checker.check_pre_trade(
                signal, portfolio, trade_value,
                data_timestamp=candles["time"].iloc[-1],
            )

            if not approved:
                record_rejection(reason)
                logger.info("trade_rejected", symbol=symbol, reason=reason)
                return

            # 10. Execute
            side = Side.BUY if signal.direction == Direction.LONG else Side.SELL
            order = await self._order_manager.submit(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_type=OrderType.MARKET,
                price=current_price,
                signal_id=f"sig_{datetime.now(UTC).strftime('%Y%m%d_%H%M')}",
            )

            record_order(side.value, order.status.value)
            logger.info(
                "order_executed",
                symbol=symbol,
                side=side.value,
                quantity=round(quantity, 6),
                price=current_price,
                status=order.status.value,
            )

        except Exception as e:
            record_error("signal_pipeline")
            logger.error("pipeline_error", symbol=symbol, error=str(e))
            raise

    async def run(self) -> None:
        """Run pipeline for all configured symbols."""
        for symbol in self._config.universe.symbols:
            await self.run_for_symbol(symbol)

        # Update portfolio metrics
        dd = self._drawdown_monitor.update(self._equity)
        update_portfolio_metrics(self._equity, dd, len(self._order_manager.open_orders))
