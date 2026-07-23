from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Iterable

from engine.assets.asset_metadata import AssetInfo, AssetMeta


class AssetCache:
    """Derived project-local asset index stored outside the source tree."""

    SCHEMA_VERSION = 1

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root).resolve() / "Library" / "AssetCache"
        self.index_path = self.root / "index.json"

    def load(self) -> dict[str, dict[str, Any]]:
        try:
            payload = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, UnicodeError, json.JSONDecodeError):
            return {}
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            return {}
        assets = payload.get("assets", {})
        return dict(assets) if isinstance(assets, dict) else {}

    def write(self, records: Iterable[tuple[AssetInfo, AssetMeta]]) -> None:
        assets = {
            info.guid: {
                "path": info.path,
                "type": info.type.value,
                "importer": meta.importer,
                "importer_version": meta.importer_version,
                "source_hash": meta.source_hash,
                "source_size": meta.source_size,
                "source_modified_ns": meta.source_modified_ns,
            }
            for info, meta in records
        }
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "assets": dict(sorted(assets.items())),
        }
        serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        self.root.mkdir(parents=True, exist_ok=True)
        if self.index_path.exists():
            try:
                if self.index_path.read_text(encoding="utf-8") == serialized:
                    return
            except (OSError, UnicodeError):
                pass
        temporary = self.root / f".index.{uuid.uuid4().hex}.tmp"
        try:
            temporary.write_text(serialized, encoding="utf-8", newline="\n")
            temporary.replace(self.index_path)
        finally:
            temporary.unlink(missing_ok=True)

    def clear(self) -> None:
        self.index_path.unlink(missing_ok=True)
