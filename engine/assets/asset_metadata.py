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

    @property
    def guid(self) -> str:
        return self.uuid


@dataclass
class AssetMeta:
    uuid: str
    type: AssetType
    importer: str
    source_path: str
    import_settings: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    schema_version: int = 1
    importer_version: int = 1
    source_hash: str = ""
    source_size: int = 0
    source_modified_ns: int = 0

    @property
    def guid(self) -> str:
        return self.uuid

    def to_dict(self) -> dict[str, Any]:
        return {
            "guid": self.uuid,
            "uuid": self.uuid,
            "type": self.type.value,
            "importer": self.importer,
            "source_path": self.source_path,
            "import_settings": self.import_settings,
            "dependencies": self.dependencies,
            "schema_version": self.schema_version,
            "importer_version": self.importer_version,
            "source_hash": self.source_hash,
            "source_size": self.source_size,
            "source_modified_ns": self.source_modified_ns,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AssetMeta":
        return cls(
            uuid=str(data.get("guid") or data["uuid"]),
            type=AssetType(str(data.get("type", AssetType.UNKNOWN.value))),
            importer=str(data.get("importer", "generic")),
            source_path=str(data.get("source_path", "")),
            import_settings=dict(data.get("import_settings", {}) or {}),
            dependencies=list(data.get("dependencies", []) or []),
            schema_version=int(data.get("schema_version", 1)),
            importer_version=int(data.get("importer_version", 0)),
            source_hash=str(data.get("source_hash", "")),
            source_size=int(data.get("source_size", 0)),
            source_modified_ns=int(data.get("source_modified_ns", 0)),
        )
