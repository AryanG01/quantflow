"""Model registry for saving and loading trained models."""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from packages.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a saved model."""

    model_id: str
    model_type: str
    created_at: str
    train_metrics: dict[str, float]
    feature_names: list[str]
    config: dict[str, object]


class ModelRegistry:
    """Save and load models with metadata."""

    def __init__(self, base_dir: str | Path = "models") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        model: object,
        model_id: str,
        model_type: str,
        train_metrics: dict[str, float],
        feature_names: list[str],
        config: dict[str, object] | None = None,
    ) -> Path:
        """Save model + metadata to disk."""
        model_dir = self._base_dir / model_id
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = model_dir / "model.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(model, f)

        metadata = ModelMetadata(
            model_id=model_id,
            model_type=model_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            train_metrics=train_metrics,
            feature_names=feature_names,
            config=config or {},
        )

        meta_path = model_dir / "metadata.json"
        with open(meta_path, "w") as f:
            json.dump(asdict(metadata), f, indent=2, default=str)

        logger.info("model_saved", model_id=model_id, path=str(model_path))
        return model_path

    def load(self, model_id: str) -> tuple[object, ModelMetadata]:
        """Load model + metadata from disk."""
        model_dir = self._base_dir / model_id

        model_path = model_dir / "model.pkl"
        with open(model_path, "rb") as f:
            model = pickle.load(f)  # noqa: S301

        meta_path = model_dir / "metadata.json"
        with open(meta_path) as f:
            meta_dict = json.load(f)
        metadata = ModelMetadata(**meta_dict)

        return model, metadata

    def list_models(self) -> list[ModelMetadata]:
        """List all saved models."""
        models = []
        for meta_path in self._base_dir.glob("*/metadata.json"):
            with open(meta_path) as f:
                meta_dict = json.load(f)
            models.append(ModelMetadata(**meta_dict))
        return models
