"""Abstract interfaces for risk management."""

from __future__ import annotations

from abc import ABC, abstractmethod

from packages.common.types import Order, PortfolioSnapshot, Signal


class RiskManager(ABC):
    """Abstract base class for risk management."""

    @abstractmethod
    def check_pre_trade(self, signal: Signal, portfolio: PortfolioSnapshot) -> tuple[bool, str]:
        """Pre-trade risk check.

        Returns:
            (approved, reason) — if not approved, reason explains why
        """

    @abstractmethod
    def compute_position_size(
        self, signal: Signal, portfolio: PortfolioSnapshot, current_price: float
    ) -> float:
        """Compute position size in base currency units."""


class PortfolioStateStore(ABC):
    """Abstract base class for portfolio state persistence."""

    @abstractmethod
    def get_snapshot(self) -> PortfolioSnapshot:
        """Get the latest portfolio snapshot."""

    @abstractmethod
    def save_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Save a portfolio snapshot."""
