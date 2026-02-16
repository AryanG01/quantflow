"""Abstract interfaces for order execution."""

from __future__ import annotations

from abc import ABC, abstractmethod

from packages.common.types import Order


class ExecutionAdapter(ABC):
    """Abstract base class for exchange execution adapters."""

    @abstractmethod
    async def submit_order(self, order: Order) -> Order:
        """Submit an order to the exchange.

        Returns:
            Updated order with exchange ID and initial status
        """

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order. Returns True if successful."""

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Order:
        """Get current order status from exchange."""

    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the exchange identifier."""
