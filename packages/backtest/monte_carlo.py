"""Monte Carlo simulation for backtest robustness testing.

Bootstrap returns and perturb parameters to generate confidence intervals.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

from packages.backtest.metrics import compute_sharpe


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""

    sharpe_ratios: npt.NDArray[np.float64]
    total_returns: npt.NDArray[np.float64]
    max_drawdowns: npt.NDArray[np.float64]
    n_simulations: int

    @property
    def sharpe_mean(self) -> float:
        return float(np.mean(self.sharpe_ratios))

    @property
    def sharpe_5th_percentile(self) -> float:
        return float(np.percentile(self.sharpe_ratios, 5))

    @property
    def sharpe_95th_percentile(self) -> float:
        return float(np.percentile(self.sharpe_ratios, 95))

    @property
    def return_5th_percentile(self) -> float:
        return float(np.percentile(self.total_returns, 5))


def bootstrap_returns(
    returns: npt.NDArray[np.float64],
    n_simulations: int = 1000,
    block_size: int = 20,
    seed: int = 42,
) -> MonteCarloResult:
    """Bootstrap block-resample returns for Monte Carlo.

    Uses block bootstrap to preserve autocorrelation structure.

    Args:
        returns: Original strategy returns
        n_simulations: Number of simulations
        block_size: Block size for bootstrap (preserves serial correlation)
        seed: Random seed

    Returns:
        MonteCarloResult with distributions of key metrics
    """
    rng = np.random.default_rng(seed)
    n = len(returns)

    sharpes = np.zeros(n_simulations)
    total_rets = np.zeros(n_simulations)
    max_dds = np.zeros(n_simulations)

    n_blocks = (n + block_size - 1) // block_size

    for sim in range(n_simulations):
        # Block bootstrap: sample blocks with replacement
        block_starts = rng.integers(0, max(1, n - block_size), size=n_blocks)
        sim_returns = np.concatenate(
            [returns[start : start + block_size] for start in block_starts]
        )[:n]

        sharpes[sim] = compute_sharpe(sim_returns)

        equity = np.cumprod(1 + sim_returns)
        total_rets[sim] = equity[-1] - 1

        peak = np.maximum.accumulate(equity)
        dd = (equity - peak) / np.maximum(peak, 1e-10)
        max_dds[sim] = abs(float(np.min(dd)))

    return MonteCarloResult(
        sharpe_ratios=sharpes,
        total_returns=total_rets,
        max_drawdowns=max_dds,
        n_simulations=n_simulations,
    )


def parameter_perturbation(
    base_params: dict[str, float],
    perturbation_pct: float = 0.20,
    n_simulations: int = 100,
    seed: int = 42,
) -> list[dict[str, float]]:
    """Generate perturbed parameter sets for robustness testing.

    Each parameter is perturbed by ±perturbation_pct.

    Args:
        base_params: Base parameter dictionary
        perturbation_pct: Maximum perturbation (0.20 = ±20%)
        n_simulations: Number of perturbed sets

    Returns:
        List of perturbed parameter dictionaries
    """
    rng = np.random.default_rng(seed)
    perturbed = []

    for _ in range(n_simulations):
        params = {}
        for key, value in base_params.items():
            factor = 1 + rng.uniform(-perturbation_pct, perturbation_pct)
            params[key] = value * factor
        perturbed.append(params)

    return perturbed
