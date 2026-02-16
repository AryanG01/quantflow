"""Binance order execution adapter using ccxt."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import ccxt.async_support as ccxt

from packages.common.errors import ExchangeError
from packages.common.logging import get_logger
from packages.common.types import Order, OrderStatus, OrderType
from packages.execution.interfaces import ExecutionAdapter

if TYPE_CHECKING:
    from packages.common.config import ExchangeConfig

logger = get_logger(__name__)


class BinanceExecutor(ExecutionAdapter):
    """Binance order execution via ccxt."""

    def __init__(self, config: ExchangeConfig, api_key: str = "", api_secret: str = "") -> None:
        self._exchange = ccxt.binance(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "sandbox": config.sandbox,
                "enableRateLimit": True,
            }
        )

    async def submit_order(self, order: Order) -> Order:
        try:
            params: dict[str, str] = {}
            if order.order_type == OrderType.MARKET:
                result = await self._exchange.create_order(
                    symbol=order.symbol,
                    type="market",
                    side=order.side.value,
                    amount=order.quantity,
                    params=params,
                )
            else:
                result = await self._exchange.create_order(
                    symbol=order.symbol,
                    type="limit",
                    side=order.side.value,
                    amount=order.quantity,
                    price=order.price,
                    params=params,
                )

            return order.model_copy(
                update={
                    "id": str(result["id"]),
                    "status": self._map_status(result.get("status", "open")),
                    "filled_qty": float(result.get("filled", 0)),
                    "avg_fill_price": float(result["average"]) if result.get("average") else None,
                    "fees": float(result.get("fee", {}).get("cost", 0)),
                }
            )
        except ccxt.BaseError as e:
            raise ExchangeError(f"Binance order submission failed: {e}") from e

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except ccxt.BaseError as e:
            logger.error("cancel_failed", order_id=order_id, error=str(e))
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Order:
        try:
            result = await self._exchange.fetch_order(order_id, symbol)
            return Order(
                id=str(result["id"]),
                time=datetime.fromtimestamp(result["timestamp"] / 1000, tz=UTC),
                symbol=symbol,
                exchange="binance",
                side=result["side"],
                order_type=result["type"],
                quantity=float(result["amount"]),
                price=float(result["price"]) if result.get("price") else None,
                status=self._map_status(result.get("status", "open")),
                filled_qty=float(result.get("filled", 0)),
                avg_fill_price=float(result["average"]) if result.get("average") else None,
                fees=float(result.get("fee", {}).get("cost", 0)),
            )
        except ccxt.BaseError as e:
            raise ExchangeError(f"Binance order status failed: {e}") from e

    def get_exchange_name(self) -> str:
        return "binance"

    async def close(self) -> None:
        await self._exchange.close()

    @staticmethod
    def _map_status(ccxt_status: str) -> OrderStatus:
        mapping = {
            "open": OrderStatus.PENDING,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        return mapping.get(ccxt_status, OrderStatus.PENDING)
