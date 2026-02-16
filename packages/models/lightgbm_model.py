"""LightGBM quantile regression model.

Trains separate models for each quantile (0.1, 0.25, 0.5, 0.75, 0.9)
to predict the distribution of future returns. The IQR (q75 - q25)
serves as an uncertainty measure for position sizing.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import lightgbm as lgb
import numpy as np
import numpy.typing as npt

from packages.common.types import PredictionResult
from packages.models.interfaces import ModelPredictor

if TYPE_CHECKING:
    import pandas as pd


class LightGBMQuantileModel(ModelPredictor):
    """LightGBM model with quantile regression for uncertainty estimation."""

    def __init__(
        self,
        quantiles: list[float] | None = None,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        max_depth: int = 6,
        num_leaves: int = 31,
    ) -> None:
        self._quantiles = quantiles or [0.1, 0.25, 0.5, 0.75, 0.9]
        self._n_estimators = n_estimators
        self._learning_rate = learning_rate
        self._max_depth = max_depth
        self._num_leaves = num_leaves
        self._models: dict[float, lgb.LGBMRegressor] = {}
        self._classifier: lgb.LGBMClassifier | None = None
        self._model_id = f"lgbm_quantile_{uuid.uuid4().hex[:8]}"
        self._feature_names: list[str] = []

    def train(self, X: pd.DataFrame, y: npt.NDArray[np.int64]) -> dict[str, float]:
        """Train quantile regression models + classifier.

        The classifier predicts the 3-class label (down/neutral/up).
        Quantile regressors predict return distribution for uncertainty.
        """
        self._feature_names = list(X.columns)

        # Train classifier for label prediction
        self._classifier = lgb.LGBMClassifier(
            n_estimators=self._n_estimators,
            learning_rate=self._learning_rate,
            max_depth=self._max_depth,
            num_leaves=self._num_leaves,
            verbose=-1,
            n_jobs=1,
        )
        self._classifier.fit(X, y)
        train_acc = float(np.mean(self._classifier.predict(X) == y))

        # Train quantile regressors (using label as continuous target)
        for q in self._quantiles:
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=self._n_estimators,
                learning_rate=self._learning_rate,
                max_depth=self._max_depth,
                num_leaves=self._num_leaves,
                verbose=-1,
                n_jobs=1,
            )
            model.fit(X, y.astype(np.float64))
            self._models[q] = model

        return {"train_accuracy": train_acc}

    def predict(self, X: pd.DataFrame) -> list[PredictionResult]:
        """Generate predictions with uncertainty estimates."""
        if self._classifier is None:
            raise RuntimeError("Model not trained")

        labels = self._classifier.predict(X).astype(np.int64)
        proba = self._classifier.predict_proba(X)

        # Quantile predictions
        q_preds: dict[float, npt.NDArray[np.float64]] = {}
        for q, model in self._models.items():
            q_preds[q] = model.predict(X).astype(np.float64)

        now = datetime.now(UTC)
        results = []
        for i in range(len(X)):
            quantiles = {f"q{int(q * 100)}": float(q_preds[q][i]) for q in self._quantiles}
            confidence = float(np.max(proba[i]))

            results.append(
                PredictionResult(
                    time=now,
                    symbol="",  # filled by caller
                    model_id=self._model_id,
                    quantiles=quantiles,
                    label=int(labels[i]),
                    confidence=confidence,
                )
            )

        return results

    def get_model_id(self) -> str:
        return self._model_id

    def feature_importance(self) -> dict[str, float]:
        if self._classifier is None:
            return {}
        importances = self._classifier.feature_importances_
        return {
            name: float(imp)
            for name, imp in zip(self._feature_names, importances, strict=True)
        }
