"""Referência estável de asset com GUID e fallback de caminho."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class AssetReference:
    guid: str = ""
    path: str = ""

    def __post_init__(self) -> None:
        if not self.guid and not self.path:
            raise ValueError("AssetReference requer guid ou path")

    @classmethod
    def from_value(cls, value: Any) -> "AssetReference":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(guid=str(value.get("guid", value.get("uuid", ""))), path=str(value.get("path", "")))
        return cls(path=str(value))

    def to_dict(self) -> dict[str, str]:
        return {key: value for key, value in {"guid": self.guid, "path": self.path}.items() if value}

    def resolve(self, database: Any) -> Path | None:
        info = database.get_asset_by_uuid(self.guid) if self.guid else None
        if info is None and self.path:
            info = database.get_asset_by_path(self.path)
        return Path(info.absolute_path) if info is not None else None
