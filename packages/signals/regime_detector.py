"""HMM-based regime detection.

Uses a 3-state Gaussian HMM on [log_returns, realized_vol] to classify
the market into trending, mean-reverting, or high-vol choppy regimes.
States are mapped by sorting on volatility characteristics.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from hmmlearn.hmm import GaussianHMM

from packages.common.logging import get_logger
from packages.common.types import Regime

logger = get_logger(__name__)


class RegimeDetector:
    """3-state Gaussian HMM regime detector."""

    def __init__(self, n_states: int = 3, n_iter: int = 100, random_state: int = 42) -> None:
        self._n_states = n_states
        self._n_iter = n_iter
        self._random_state = random_state
        self._model: GaussianHMM | None = None
        self._state_to_regime: dict[int, Regime] = {}

    def fit(
        self, log_returns: npt.NDArray[np.float64], realized_vol: npt.NDArray[np.float64]
    ) -> None:
        """Fit the HMM on historical features.

        Args:
            log_returns: Array of log returns
            realized_vol: Array of realized volatility
        """
        X = np.column_stack([log_returns, realized_vol])

        # Remove NaN rows
        valid = ~np.isnan(X).any(axis=1)
        X_clean = X[valid]

        if len(X_clean) < 100:
            logger.warning("insufficient_data_for_hmm", n_samples=len(X_clean))
            return

        self._model = GaussianHMM(
            n_components=self._n_states,
            covariance_type="full",
            n_iter=self._n_iter,
            random_state=self._random_state,
        )
        self._model.fit(X_clean)
        self._map_states_to_regimes()

        logger.info(
            "regime_detector_fitted",
            n_samples=len(X_clean),
            state_mapping={r.value: s for s, r in self._state_to_regime.items()},
        )

    def _map_states_to_regimes(self) -> None:
        """Map HMM states to regime labels based on volatility characteristics.

        - Highest vol state → choppy
        - Lowest vol state → trending (clean moves)
        - Middle → mean_reverting
        """
        if self._model is None:
            return

        # Sort states by mean volatility (second feature)
        means = self._model.means_
        vol_means = means[:, 1]  # realized_vol column
        sorted_states = np.argsort(vol_means)

        self._state_to_regime = {
            int(sorted_states[0]): Regime.TRENDING,  # lowest vol
            int(sorted_states[1]): Regime.MEAN_REVERTING,  # medium vol
            int(sorted_states[2]): Regime.CHOPPY,  # highest vol
        }

    def predict(
        self, log_returns: npt.NDArray[np.float64], realized_vol: npt.NDArray[np.float64]
    ) -> list[Regime]:
        """Predict regime for each observation.

        Args:
            log_returns: Array of log returns
            realized_vol: Array of realized volatility

        Returns:
            List of Regime enums
        """
        if self._model is None:
            return [Regime.CHOPPY] * len(log_returns)

        X = np.column_stack([log_returns, realized_vol])
        valid = ~np.isnan(X).any(axis=1)

        regimes = [Regime.CHOPPY] * len(log_returns)
        if valid.sum() > 0:
            states = self._model.predict(X[valid])
            valid_idx = np.where(valid)[0]
            for i, state in zip(valid_idx, states, strict=True):
                regimes[i] = self._state_to_regime.get(int(state), Regime.CHOPPY)

        return regimes

    def predict_current(
        self, log_returns: npt.NDArray[np.float64], realized_vol: npt.NDArray[np.float64]
    ) -> Regime:
        """Predict regime for the most recent observation."""
        regimes = self.predict(log_returns, realized_vol)
        return regimes[-1] if regimes else Regime.CHOPPY
