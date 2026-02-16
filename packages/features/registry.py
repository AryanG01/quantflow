"""Feature metadata and versioning registry."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FeatureMetadata:
    """Metadata for a feature set."""

    name: str
    version: int
    feature_names: list[str]
    description: str = ""
    dependencies: list[str] = field(default_factory=list)


class FeatureRegistry:
    """Registry for managing feature set metadata and versions."""

    def __init__(self) -> None:
        self._features: dict[str, FeatureMetadata] = {}

    def register(self, metadata: FeatureMetadata) -> None:
        self._features[metadata.name] = metadata

    def get(self, name: str) -> FeatureMetadata | None:
        return self._features.get(name)

    def list_all(self) -> list[FeatureMetadata]:
        return list(self._features.values())

    def get_version(self, name: str) -> int:
        meta = self._features.get(name)
        return meta.version if meta else 0
