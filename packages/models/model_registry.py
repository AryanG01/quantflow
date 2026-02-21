"""Model registry for saving and loading trained models."""

from __future__ import annotations

import json
import pickle
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import sqlalchemy as sa

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
            created_at=datetime.now(UTC).isoformat(),
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

    def save_to_db(
        self,
        engine: sa.engine.Engine,
        model: object,
        model_id: str,
        model_type: str,
        train_metrics: dict[str, float],
        feature_names: list[str],
        config: dict[str, object] | None = None,
    ) -> None:
        """Pickle model and store as BYTEA in model_artifacts table (upsert)."""
        artifact = pickle.dumps(model)
        metadata = {
            "model_id": model_id,
            "model_type": model_type,
            "created_at": datetime.now(UTC).isoformat(),
            "train_metrics": train_metrics,
            "feature_names": feature_names,
            "config": config or {},
        }
        sql = sa.text(
            """
            INSERT INTO model_artifacts (model_id, model_type, artifact, metadata, created_at)
            VALUES (:model_id, :model_type, :artifact, :metadata::jsonb, NOW())
            ON CONFLICT (model_id) DO UPDATE
                SET model_type = EXCLUDED.model_type,
                    artifact   = EXCLUDED.artifact,
                    metadata   = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
            """
        )
        with engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "model_id": model_id,
                    "model_type": model_type,
                    "artifact": artifact,
                    "metadata": json.dumps(metadata, default=str),
                },
            )
        logger.info("model_saved_to_db", model_id=model_id)

    def load_from_db(self, engine: sa.engine.Engine, model_id: str) -> tuple[object, ModelMetadata]:
        """Load pickled model from model_artifacts table."""
        sql = sa.text("SELECT artifact, metadata FROM model_artifacts WHERE model_id = :model_id")
        with engine.connect() as conn:
            row = conn.execute(sql, {"model_id": model_id}).fetchone()
        if row is None:
            raise FileNotFoundError(f"No DB model found for model_id={model_id}")
        artifact_bytes, meta_dict = row
        model = pickle.loads(artifact_bytes)  # noqa: S301
        if isinstance(meta_dict, str):
            meta_dict = json.loads(meta_dict)
        metadata = ModelMetadata(**meta_dict)
        logger.info("model_loaded_from_db", model_id=model_id)
        return model, metadata
