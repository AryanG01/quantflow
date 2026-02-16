"""Feature drift monitoring using PSI."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from packages.common.logging import get_logger
from packages.models.drift_detector import compute_psi

logger = get_logger(__name__)


class DriftMonitor:
    """Monitor feature distributions for drift using PSI."""

    def __init__(self, psi_threshold: float = 0.2) -> None:
        self._psi_threshold = psi_threshold
        self._reference_data: dict[str, npt.NDArray[np.float64]] = {}

    def set_reference(self, features: pd.DataFrame) -> None:
        """Set reference distributions from training data."""
        for col in features.columns:
            values = features[col].dropna().values.astype(np.float64)
            if len(values) > 0:
                self._reference_data[col] = values

    def check_drift(self, current: pd.DataFrame) -> dict[str, float]:
        """Check PSI for all features against reference.

        Returns:
            Dict of feature_name -> PSI value. Values > threshold indicate drift.
        """
        results = {}
        for col in current.columns:
            if col not in self._reference_data:
                continue

            current_values = current[col].dropna().values.astype(np.float64)
            if len(current_values) < 10:
                continue

            psi = compute_psi(self._reference_data[col], current_values)
            results[col] = psi

            if psi > self._psi_threshold:
                logger.warning("feature_drift_detected", feature=col, psi=round(psi, 4))

        return results
