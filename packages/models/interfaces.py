"""Abstract interfaces for ML models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt
    import pandas as pd

    from packages.common.types import PredictionResult


class ModelPredictor(ABC):
    """Abstract base class for ML prediction models."""

    @abstractmethod
    def train(self, X: pd.DataFrame, y: npt.NDArray[np.int64]) -> dict[str, float]:
        """Train the model on feature matrix X and labels y.

        Returns:
            Training metrics dict (e.g., accuracy, loss)
        """

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """Generate predictions for feature matrix X."""

    @abstractmethod
    def get_model_id(self) -> str:
        """Return unique identifier for this model instance."""

    @abstractmethod
    def feature_importance(self) -> dict[str, float]:
        """Return feature importance scores."""
