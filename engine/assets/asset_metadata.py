from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engine.assets.asset_types import AssetType


@dataclass(frozen=True)
class AssetInfo:
    uuid: str
    name: str
    path: str
    absolute_path: Path
    type: AssetType
    extension: str
    size: int
    modified_time: float
    metadata_path: Path


@dataclass
class AssetMeta:
    uuid: str
    type: AssetType
    importer: str
    source_path: str
    import_settings: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uuid": self.uuid,
            "type": self.type.value,
            "importer": self.importer,
            "source_path": self.source_path,
            "import_settings": self.import_settings,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetMeta":
        return cls(
            uuid=str(data["uuid"]),
            type=AssetType(str(data.get("type", AssetType.UNKNOWN.value))),
            importer=str(data.get("importer", "generic")),
            source_path=str(data.get("source_path", "")),
            import_settings=dict(data.get("import_settings", {}) or {}),
            dependencies=list(data.get("dependencies", []) or []),
        )
