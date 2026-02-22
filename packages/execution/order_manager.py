"""Order lifecycle management with paper and live modes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from packages.common.errors import ExchangeError
from packages.common.logging import get_logger
from packages.common.types import Order, OrderStatus, OrderType, Side

if TYPE_CHECKING:
    from packages.execution.interfaces import ExecutionAdapter

logger = get_logger(__name__)


class OrderManager:
    """Manages order lifecycle: paper mode (simulated) and live mode."""

    def __init__(
        self,
        executor: ExecutionAdapter | None = None,
        paper_mode: bool = True,
        max_retries: int = 3,
        timeout_seconds: int = 120,
        slippage_bps: float = 5.0,
        fee_rate: float = 0.001,
    ) -> None:
        self._executor = executor
        self._paper_mode = paper_mode
        self._max_retries = max_retries
        self._timeout_seconds = timeout_seconds
        self._slippage_bps = slippage_bps
        self._fee_rate = fee_rate
        self._open_orders: dict[str, Order] = {}

    async def submit(
        self,
        symbol: str,
        side: Side,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: float | None = None,
        signal_id: str | None = None,
    ) -> Order:
        """Submit a new order (paper or live)."""
        order = Order(
            id=f"ord_{uuid.uuid4().hex[:12]}",
            time=datetime.now(UTC),
            symbol=symbol,
            exchange="paper"
            if self._paper_mode
            else (self._executor.get_exchange_name() if self._executor else "unknown"),
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            signal_id=signal_id,
        )

        if self._paper_mode:
            return self._simulate_fill(order)

        if self._executor is None:
            raise ExchangeError("No executor configured for live mode")

        filled_order = await self._executor.submit_order(order)
        self._open_orders[filled_order.id] = filled_order

        logger.info(
            "order_submitted",
            order_id=filled_order.id,
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            status=filled_order.status.value,
        )
        return filled_order

    def _simulate_fill(self, order: Order) -> Order:
        """Simulate an immediate fill for paper trading.

        Applies a half-spread slippage: buys fill slightly above price,
        sells slightly below, using the configured slippage_bps.
        """
        fill_price = order.price if order.price and order.price > 0 else 0.0

        if fill_price > 0 and self._slippage_bps > 0:
            slip = self._slippage_bps / 10_000.0
            if order.side == Side.BUY:
                fill_price *= 1.0 + slip
            else:
                fill_price *= 1.0 - slip

        fees = fill_price * order.quantity * self._fee_rate if fill_price > 0 else 0.0
        filled = order.model_copy(
            update={
                "status": OrderStatus.FILLED,
                "filled_qty": order.quantity,
                "avg_fill_price": fill_price,
                "fees": fees,
            }
        )

        logger.info(
            "paper_order_filled",
            order_id=filled.id,
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            price=fill_price,
        )
        return filled

    async def check_open_orders(self) -> list[Order]:
        """Poll status of all open orders."""
        if self._paper_mode or self._executor is None:
            return []

        updated = []
        for order_id, order in list(self._open_orders.items()):
            try:
                current = await self._executor.get_order_status(order_id, order.symbol)
                self._open_orders[order_id] = current

                if current.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
                    del self._open_orders[order_id]

                updated.append(current)
            except ExchangeError as e:
                logger.error("order_check_failed", order_id=order_id, error=str(e))

        return updated

    @property
    def open_orders(self) -> dict[str, Order]:
        return dict(self._open_orders)
