"""Transaction cost models for backtesting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

if TYPE_CHECKING:
    from packages.common.config import ExchangeFees, SlippageModelConfig


@dataclass(frozen=True)
class CostModelConfig:
    """Cost model parameters."""

    fixed_spread_bps: float = 5.0
    linear_impact_bps: float = 2.0
    maker_fee_bps: float = 10.0
    taker_fee_bps: float = 10.0

    @classmethod
    def from_app_config(
        cls,
        slippage: SlippageModelConfig,
        fees: ExchangeFees,
    ) -> CostModelConfig:
        """Build from AppConfig slippage and exchange fee sub-configs."""
        return cls(
            fixed_spread_bps=slippage.fixed_spread_bps,
            linear_impact_bps=slippage.linear_impact_bps,
            maker_fee_bps=fees.maker,
            taker_fee_bps=fees.taker,
        )


class CostModel:
    """Compute transaction costs including spread, impact, and fees.

    Total cost per trade (in bps):
        slippage = fixed_spread_bps + linear_impact_bps * (trade_pct_of_adv)
        fees = taker_fee_bps  (assume taker for market orders)
        total = slippage + fees
    """

    def __init__(self, config: CostModelConfig | None = None) -> None:
        self._config = config or CostModelConfig()

    def compute_costs_bps(
        self,
        trade_values: npt.NDArray[np.float64],
        adv_values: npt.NDArray[np.float64],
        is_maker: bool = False,
    ) -> npt.NDArray[np.float64]:
        """Compute total transaction costs in basis points.

        Args:
            trade_values: Absolute dollar value of each trade
            adv_values: Average daily volume in dollars for each bar
            is_maker: If True, use maker fee instead of taker fee

        Returns:
            Array of total costs in basis points per trade
        """
        safe_adv = np.maximum(adv_values, 1.0)  # avoid division by zero
        trade_pct_of_adv = trade_values / safe_adv

        slippage = self._config.fixed_spread_bps + (
            self._config.linear_impact_bps * trade_pct_of_adv
        )
        fees = self._config.maker_fee_bps if is_maker else self._config.taker_fee_bps

        return slippage + fees

    def compute_costs_pct(
        self,
        trade_values: npt.NDArray[np.float64],
        adv_values: npt.NDArray[np.float64],
        is_maker: bool = False,
    ) -> npt.NDArray[np.float64]:
        """Compute costs as a fraction (e.g., 0.0015 = 15 bps)."""
        return self.compute_costs_bps(trade_values, adv_values, is_maker=is_maker) / 10_000.0
