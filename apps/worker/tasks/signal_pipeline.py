"""End-to-end signal generation pipeline.

Runs every 4h: candles → features → predict → regime → fuse → risk → size → execute.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

from packages.common.logging import get_logger
from packages.common.types import Direction, OrderStatus, OrderType, PortfolioSnapshot, Side
from packages.execution.order_manager import OrderManager
from packages.features.normalizer import RollingZScoreNormalizer
from packages.features.technical import TechnicalFeatures
from packages.models.labeling import triple_barrier_labels
from packages.models.lightgbm_model import LightGBMQuantileModel
from packages.models.model_registry import ModelRegistry
from packages.monitoring.metrics_exporter import (
    record_error,
    record_order,
    record_rejection,
    signal_strength_gauge,
    update_portfolio_metrics,
)
from packages.risk.drawdown_monitor import DrawdownMonitor
from packages.risk.portfolio_state import DBPortfolioStateStore
from packages.risk.position_sizer import VolTargetPositionSizer
from packages.risk.risk_checks import RiskChecker
from packages.signals.regime_detector import RegimeDetector
from packages.signals.sentiment_scorer import SentimentScorer
from packages.signals.signal_fusion import RegimeGatedMoE

if TYPE_CHECKING:
    from packages.common.config import AppConfig

logger = get_logger(__name__)

# ── DB table references (match migration schema) ─────────────

_meta = sa.MetaData()

_signals_table = sa.Table(
    "signals",
    _meta,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("symbol", sa.Text),
    sa.Column("direction", sa.Text),
    sa.Column("strength", sa.Float),
    sa.Column("confidence", sa.Float),
    sa.Column("regime", sa.Text),
    sa.Column("components", sa.JSON),
)

_orders_table = sa.Table(
    "orders",
    _meta,
    sa.Column("id", sa.Text, primary_key=True),
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
    sa.Column("signal_strength", sa.Float),
    sa.Column("signal_regime", sa.Text),
    sa.Column("realized_pnl", sa.Float),
)

_positions_table = sa.Table(
    "positions",
    _meta,
    sa.Column("symbol", sa.Text, primary_key=True),
    sa.Column("exchange", sa.Text),
    sa.Column("side", sa.Text),
    sa.Column("quantity", sa.Float),
    sa.Column("avg_entry_price", sa.Float),
    sa.Column("unrealized_pnl", sa.Float),
    sa.Column("realized_pnl", sa.Float),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)

_risk_table = sa.Table(
    "risk_metrics",
    _meta,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("max_drawdown_pct", sa.Float),
    sa.Column("current_drawdown_pct", sa.Float),
    sa.Column("portfolio_vol", sa.Float),
    sa.Column("sharpe_ratio", sa.Float),
    sa.Column("concentration_pct", sa.Float),
    sa.Column("kill_switch_active", sa.Boolean),
)

_portfolio_snapshots_table = sa.Table(
    "portfolio_snapshots",
    _meta,
    sa.Column("time", sa.DateTime(timezone=True)),
    sa.Column("equity", sa.Float),
)


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
            bars_per_year=tech_cfg.bars_per_year,
        )
        norm_cfg = config.features.normalization
        self._normalizer = RollingZScoreNormalizer(window=norm_cfg.window, shift=norm_cfg.shift)

        # ML model (retrained periodically, loaded from registry in production)
        self._model = LightGBMQuantileModel(
            quantiles=config.model.quantiles,
            n_estimators=config.model.n_estimators,
            learning_rate=config.model.learning_rate,
            max_depth=config.model.max_depth,
            num_leaves=config.model.num_leaves,
        )
        self._model_trained = False
        self._model_registry = ModelRegistry(base_dir="models")

        # Attempt to load a previously saved model at startup (disk first, then DB)
        try:
            saved_model, _metadata = self._model_registry.load("lightgbm_latest")
            self._model = saved_model  # type: ignore[assignment]
            self._model_trained = True
            logger.info("model_loaded_from_registry", model_id="lightgbm_latest")
        except (FileNotFoundError, OSError):
            logger.info("no_disk_model_found, trying db")
            try:
                saved_model, _metadata = self._model_registry.load_from_db(
                    engine, "lightgbm_latest"
                )
                self._model = saved_model  # type: ignore[assignment]
                self._model_trained = True
                logger.info("model_loaded_from_db")
            except Exception:
                logger.info("no_db_model, will train from scratch")

        # Regime detection
        self._regime_detector = RegimeDetector(n_states=config.regime.n_states)
        self._regime_fitted = False

        # Signal fusion
        self._fusioner = RegimeGatedMoE(config.signals.fusion)

        # Sentiment scorer — wired to app-level SentimentConfig
        from packages.signals.sentiment_scorer import SentimentConfig

        self._sentiment_scorer = SentimentScorer(
            SentimentConfig(
                decay_halflife_hours=config.sentiment.decay_halflife_hours,
                max_events_per_source=config.sentiment.max_events_per_source,
                staleness_hours=config.sentiment.staleness_hours,
                dedup_window_hours=config.sentiment.dedup_window_hours,
            )
        )

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
        self._drawdown_monitor = DrawdownMonitor(max_drawdown_pct=config.risk.max_drawdown_pct)
        # Seed peak equity from historical max so kill switch survives restarts
        try:
            with engine.connect() as _conn:
                row = _conn.execute(
                    sa.text("SELECT MAX(equity) FROM portfolio_snapshots")
                ).fetchone()
                if row and row[0] is not None:
                    self._drawdown_monitor._peak_equity = float(row[0])
                    logger.info("drawdown_monitor_peak_seeded", peak_equity=row[0])
        except Exception:
            pass  # No snapshots yet; peak will be set on first update

        # Execution — apply half-spread slippage on paper fills
        self._order_manager = OrderManager(
            paper_mode=(config.execution.mode == "paper"),
            slippage_bps=config.execution.slippage_model.fixed_spread_bps,
        )

        # Portfolio state backed by TimescaleDB
        self._portfolio_store = DBPortfolioStateStore(
            engine, initial_equity=config.portfolio.initial_equity
        )

        # Write initial snapshot so API shows LIVE (not demo) immediately on startup
        existing = self._portfolio_store.get_snapshot()
        if (
            existing.equity == config.portfolio.initial_equity
            and existing.cash == config.portfolio.initial_equity
        ):
            self._portfolio_store.save_snapshot(existing)
            logger.info("initial_portfolio_snapshot_written", equity=existing.equity)

        # A1: Restore kill switch if prior drawdown exceeded threshold (survives restarts)
        try:
            snapshot = self._portfolio_store.get_snapshot()
            if snapshot.drawdown_pct >= config.risk.max_drawdown_pct:
                self._risk_checker._kill_switch_active = True
                logger.critical("kill_switch_restored_from_db", drawdown_pct=snapshot.drawdown_pct)
        except Exception:
            pass  # No snapshot yet; kill switch will be set on first drawdown breach

    # ── DB helpers ────────────────────────────────────────────

    def _compute_portfolio_stats(self) -> tuple[float, float | None]:
        """Compute annualized volatility and Sharpe from portfolio snapshot history.

        Uses the last `vol_lookback_bars` equity snapshots. Returns (0.0, None)
        when there is insufficient history.
        """
        n_bars = self._config.portfolio.vol_lookback_bars
        query = sa.text("SELECT equity FROM portfolio_snapshots ORDER BY time DESC LIMIT :n")
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(query, {"n": n_bars}).fetchall()
        except Exception:
            return 0.0, None

        if len(rows) < 5:
            return 0.0, None

        # Rows are DESC; reverse for chronological order
        equities = np.array([r[0] for r in reversed(rows)], dtype=np.float64)
        log_returns = np.diff(np.log(np.maximum(equities, 1e-10)))

        std = float(np.std(log_returns))
        if std == 0.0:
            return 0.0, None

        bars_per_year = self._config.features.technical.bars_per_year
        ann_factor = float(np.sqrt(bars_per_year))
        vol = std * ann_factor
        sharpe = float(np.mean(log_returns)) / std * ann_factor
        return vol, sharpe

    def _taker_fee_rate(self) -> float:
        """Return taker fee as a fraction from config (e.g. 10 bps → 0.001)."""
        from packages.common.config import ExchangeConfig

        exchange_cfg = self._config.exchanges.get("binance", ExchangeConfig())
        return exchange_cfg.fees_bps.taker / 10_000.0

    def _persist_signal(
        self, signal: object, components: dict[str, float], regime_value: str
    ) -> None:
        """Write a signal row to the signals table."""
        from packages.common.types import Signal

        sig: Signal = signal  # type: ignore[assignment]
        try:
            with self._engine.begin() as conn:
                conn.execute(
                    _signals_table.insert().values(
                        time=sig.time,
                        symbol=sig.symbol,
                        direction=sig.direction.value,
                        strength=sig.strength,
                        confidence=sig.confidence,
                        regime=regime_value,
                        components=components,
                    )
                )
            logger.debug("signal_persisted", symbol=sig.symbol)
        except Exception as e:
            logger.warning("signal_persist_failed", error=str(e))

    def _persist_order(
        self,
        order: object,
        price: float,
        signal_strength: float = 0.0,
        signal_regime: str = "unknown",
        realized_pnl: float = 0.0,
    ) -> None:
        """Write an order row to the orders table."""
        from packages.common.types import Order

        o: Order = order  # type: ignore[assignment]
        try:
            with self._engine.begin() as conn:
                conn.execute(
                    pg_insert(_orders_table)
                    .values(
                        id=o.id,
                        time=o.time,
                        symbol=o.symbol,
                        exchange=o.exchange,
                        side=o.side.value,
                        order_type=o.order_type.value,
                        quantity=o.quantity,
                        price=price,
                        status=o.status.value,
                        filled_qty=o.filled_qty,
                        avg_fill_price=o.avg_fill_price,
                        fees=o.fees,
                        signal_id=o.signal_id,
                        signal_strength=signal_strength,
                        signal_regime=signal_regime,
                        realized_pnl=realized_pnl,
                    )
                    .on_conflict_do_nothing()
                )
            logger.debug("order_persisted", order_id=o.id)
        except Exception as e:
            logger.warning("order_persist_failed", error=str(e))

    def _get_existing_quantity(self, symbol: str) -> float:
        """Return current open quantity for a symbol from the positions table."""
        query = sa.select(_positions_table.c.quantity).where(_positions_table.c.symbol == symbol)
        try:
            with self._engine.connect() as conn:
                row = conn.execute(query).fetchone()
            if row and row[0] is not None:
                return float(row[0])
        except Exception:
            pass
        return 0.0

    def _get_position_entry_price(self, symbol: str) -> float | None:
        """Look up current avg_entry_price for a symbol from positions table."""
        query = sa.select(_positions_table.c.avg_entry_price).where(
            _positions_table.c.symbol == symbol
        )
        try:
            with self._engine.connect() as conn:
                row = conn.execute(query).fetchone()
            if row and row[0]:
                return float(row[0])
        except Exception:
            pass
        return None

    def _persist_position(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: float,
        avg_entry_price: float,
        unrealized_pnl: float,
        realized_pnl: float,
    ) -> None:
        """Upsert a position row (PostgreSQL ON CONFLICT)."""
        try:
            stmt = pg_insert(_positions_table).values(
                symbol=symbol,
                exchange=exchange,
                side=side,
                quantity=quantity,
                avg_entry_price=avg_entry_price,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                updated_at=datetime.now(UTC),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "side": stmt.excluded.side,
                    "quantity": stmt.excluded.quantity,
                    "avg_entry_price": stmt.excluded.avg_entry_price,
                    "unrealized_pnl": stmt.excluded.unrealized_pnl,
                    "realized_pnl": stmt.excluded.realized_pnl,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            with self._engine.begin() as conn:
                conn.execute(stmt)
            logger.debug("position_upserted", symbol=symbol)
        except Exception as e:
            logger.warning("position_persist_failed", error=str(e))

    def _persist_risk_metrics(self) -> None:
        """Write current risk metrics to the risk_metrics table."""
        snapshot = self._portfolio_store.get_snapshot()
        portfolio_vol, sharpe_ratio = self._compute_portfolio_stats()
        try:
            with self._engine.begin() as conn:
                conn.execute(
                    _risk_table.insert().values(
                        time=datetime.now(UTC),
                        max_drawdown_pct=self._config.risk.max_drawdown_pct,
                        current_drawdown_pct=self._drawdown_monitor.current_drawdown,
                        portfolio_vol=portfolio_vol,
                        sharpe_ratio=sharpe_ratio,
                        concentration_pct=(
                            snapshot.positions_value / snapshot.equity * 100
                            if snapshot.equity > 0
                            else 0.0
                        ),
                        kill_switch_active=self._risk_checker.kill_switch_active,
                    )
                )
            logger.debug("risk_metrics_persisted")
        except Exception as e:
            logger.warning("risk_metrics_persist_failed", error=str(e))

    # ── Data fetching ─────────────────────────────────────────

    def _fetch_candles(self, symbol: str) -> pd.DataFrame:
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
                {
                    "symbol": symbol,
                    "timeframe": self._config.universe.timeframe,
                    "limit": self._config.portfolio.signal_lookback_bars,
                },
            )
            rows = result.fetchall()

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
        return df.sort_values("time").reset_index(drop=True)

    # ── Training ──────────────────────────────────────────────

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

        if len(clean_features) < self._config.portfolio.min_train_bars:
            logger.warning("insufficient_data_for_training", n=len(clean_features))
            return

        # Train regime detector
        if not self._regime_fitted:
            log_ret = features["log_returns"].values[valid_mask.to_numpy()]
            real_vol = features["realized_vol"].values[valid_mask.to_numpy()]
            self._regime_detector.fit(log_ret, real_vol)
            self._regime_fitted = True

        # Train ML model
        if not self._model_trained:
            labels = triple_barrier_labels(
                clean_candles["close"],
                config=self._config.model.labeling,
            )
            valid_labels = labels >= 0
            if valid_labels.sum() > self._config.portfolio.min_valid_labels:
                self._model.train(
                    clean_features[valid_labels],
                    labels[valid_labels],
                )
                self._model_trained = True
                logger.info("model_trained", n_samples=int(valid_labels.sum()))

                # Persist trained model to disk and DB
                feature_names = list(clean_features.columns)
                train_metrics: dict[str, float] = {"n_samples": float(valid_labels.sum())}
                try:
                    self._model_registry.save(
                        model=self._model,
                        model_id="lightgbm_latest",
                        model_type="lightgbm_quantile",
                        train_metrics=train_metrics,
                        feature_names=feature_names,
                    )
                    logger.info("model_saved_to_registry", model_id="lightgbm_latest")
                except Exception as e:
                    logger.warning("model_disk_save_failed", error=str(e))
                try:
                    self._model_registry.save_to_db(
                        engine=self._engine,
                        model=self._model,
                        model_id="lightgbm_latest",
                        model_type="lightgbm_quantile",
                        train_metrics=train_metrics,
                        feature_names=feature_names,
                    )
                except Exception as e:
                    logger.warning("model_db_save_failed", error=str(e))

    # ── Pipeline execution ────────────────────────────────────

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
                # Use classifier max-class probability as confidence [0.33, 1.0].
                # IQR on integer labels {0,1,2} degenerates to q25=0, q75=2 → IQR=2
                # which causes uncertainty_to_confidence() to return 0 regardless
                # of the config ceiling. pred.confidence = np.max(predict_proba())
                # is always ≥ 0.33 for 3 classes and never zeros out signals.
                confidence = pred.confidence
                ml_score = (pred.label - 1) / 1.0  # map 0,1,2 → -1,0,1
            else:
                confidence = 0.5
                ml_score = 0.0

            # 5. Detect regime (drop NaN jointly so both arrays stay same length)
            regime_df = features[["log_returns", "realized_vol"]].dropna()
            log_ret = regime_df["log_returns"].values
            real_vol = regime_df["realized_vol"].values
            regime = self._regime_detector.predict_current(log_ret, real_vol)

            # 6. Technical signal (composite: RSI + BB%B + VWAP deviation)
            rsi = features["rsi"].iloc[-1]
            bb_pct_b = features["bb_pct_b"].iloc[-1]
            vwap_dev = features["vwap_deviation"].iloc[-1]
            rsi_score = float(np.clip((50 - rsi) / 50, -1, 1)) if pd.notna(rsi) else 0.0
            bb_score = float(np.clip((0.5 - bb_pct_b) * 2, -1, 1)) if pd.notna(bb_pct_b) else 0.0
            vwap_score = float(np.clip(-vwap_dev * 20, -1, 1)) if pd.notna(vwap_dev) else 0.0
            tech_score = 0.4 * rsi_score + 0.3 * bb_score + 0.3 * vwap_score

            # 7. Fuse signals (with live sentiment)
            sentiment_score = self._sentiment_scorer.compute_score(symbol)
            components = {
                "technical": tech_score,
                "ml": ml_score,
                "sentiment": sentiment_score,
            }
            signal = self._fusioner.combine(components, regime, confidence, symbol)

            # 7b. Persist signal to DB
            self._persist_signal(signal, components, regime.value)

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
            portfolio = self._portfolio_store.get_snapshot()

            # 9. Position sizing
            realized_vol = (
                float(features["realized_vol"].iloc[-1])
                if pd.notna(features["realized_vol"].iloc[-1])
                else 0.3
            )
            quantity = self._position_sizer.compute_size(
                signal, portfolio, current_price, realized_vol
            )

            # B2: Delta sizing — only trade the difference vs existing position
            existing_qty = self._get_existing_quantity(symbol)
            quantity = max(0.0, quantity - existing_qty)

            if quantity < 1e-8 or signal.direction == Direction.FLAT:
                return  # Skip flat or negligible signals

            trade_value = quantity * current_price
            approved, reason = self._risk_checker.check_pre_trade(
                signal,
                portfolio,
                trade_value,
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

            # 10b. Compute realized PnL and update portfolio state after fill
            trade_realized_pnl = 0.0
            if order.status == OrderStatus.FILLED:
                fill_price = order.avg_fill_price or current_price
                fill_cost = fill_price * order.filled_qty
                fees = fill_cost * self._taker_fee_rate()

                if side == Side.SELL:
                    entry_price = self._get_position_entry_price(symbol)
                    if entry_price and entry_price > 0:
                        trade_realized_pnl = (fill_price - entry_price) * order.filled_qty - fees

            # 10c. Persist order with signal metadata
            self._persist_order(
                order,
                current_price,
                signal_strength=signal.strength,
                signal_regime=regime.value,
                realized_pnl=trade_realized_pnl,
            )

            # 10d. Update portfolio state after fill
            if order.status == OrderStatus.FILLED:
                prev = portfolio
                if side == Side.BUY:
                    new_cash = prev.cash - fill_cost - fees
                    new_positions_value = prev.positions_value + fill_cost
                else:
                    new_cash = prev.cash + fill_cost - fees
                    new_positions_value = max(0.0, prev.positions_value - fill_cost)

                new_equity = new_cash + new_positions_value
                dd = self._drawdown_monitor.update(new_equity)

                new_snapshot = PortfolioSnapshot(
                    time=datetime.now(UTC),
                    equity=new_equity,
                    cash=new_cash,
                    positions_value=new_positions_value,
                    unrealized_pnl=0.0,
                    realized_pnl=prev.realized_pnl + trade_realized_pnl,
                    drawdown_pct=dd,
                )
                self._portfolio_store.save_snapshot(new_snapshot)

                # 10e. Upsert position
                pos_side = signal.direction.value
                self._persist_position(
                    symbol=symbol,
                    exchange=order.exchange,
                    side=pos_side,
                    quantity=order.filled_qty,
                    avg_entry_price=fill_price,
                    unrealized_pnl=0.0,
                    realized_pnl=trade_realized_pnl,
                )

        except Exception as e:
            record_error("signal_pipeline")
            logger.error("pipeline_error", symbol=symbol, error=str(e))
            # Do not re-raise — let other symbols continue

    async def run(self) -> None:
        """Run pipeline for all configured symbols."""
        for symbol in self._config.universe.symbols:
            await self.run_for_symbol(symbol)

        # Update portfolio metrics from DB-backed store
        snapshot = self._portfolio_store.get_snapshot()
        dd = self._drawdown_monitor.update(snapshot.equity)
        update_portfolio_metrics(snapshot.equity, dd, len(self._order_manager.open_orders))

        # Persist risk metrics
        self._persist_risk_metrics()

        # Write snapshot every run so equity curve builds even with no trades
        updated = snapshot.model_copy(update={"time": datetime.now(UTC), "drawdown_pct": dd})
        self._portfolio_store.save_snapshot(updated)
        logger.info("portfolio_snapshot_written", equity=snapshot.equity, drawdown=dd)
