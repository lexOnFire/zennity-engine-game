from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Iterable

from engine.assets.asset_importer import ImporterRegistry
from engine.assets.asset_metadata import AssetInfo, AssetMeta
from engine.assets.asset_types import AssetType
from engine.serialization_registry import atomic_write_json


class AssetDatabase:
    """Scans the project Assets directory and maintains .meta files."""

    DEFAULT_FOLDERS = (
        "Scenes",
        "Prefabs",
        "Scripts",
        "Textures",
        "Audio",
        "Animations",
        "Materials",
        "Meshes",
    )

    def __init__(self, project_root: str | Path | None = None, assets_dir: str = "Assets") -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.assets_root = (self.project_root / assets_dir).resolve()
        self.importer_registry = ImporterRegistry()
        self._assets_by_uuid: dict[str, AssetInfo] = {}
        self._assets_by_path: dict[str, AssetInfo] = {}

    def scan(self) -> list[AssetInfo]:
        self.ensure_project_folders()
        self._assets_by_uuid.clear()
        self._assets_by_path.clear()

        for path in self._iter_asset_files():
            info = self.import_asset(path)
            self._assets_by_uuid[info.uuid] = info
            self._assets_by_path[info.path] = info

        return self.list_assets()

    def ensure_project_folders(self) -> None:
        self.assets_root.mkdir(parents=True, exist_ok=True)
        for folder in self.DEFAULT_FOLDERS:
            (self.assets_root / folder).mkdir(parents=True, exist_ok=True)

    def refresh(self) -> list[AssetInfo]:
        self.remove_missing_assets()
        return self.scan()

    def get_asset_by_uuid(self, asset_uuid: str) -> AssetInfo | None:
        return self._assets_by_uuid.get(asset_uuid)

    def get_asset_by_path(self, path: str | Path) -> AssetInfo | None:
        return self._assets_by_path.get(self._relative_asset_path(path))

    def reference_for(self, path: str | Path):
        """Cria referência GUID + path, mantendo fallback para projetos antigos."""
        from engine.assets.reference import AssetReference
        info = self.get_asset_by_path(path)
        if info is None:
            info = self.import_asset(path)
        return AssetReference(guid=info.uuid, path=info.path)

    def list_assets(self) -> list[AssetInfo]:
        return sorted(self._assets_by_uuid.values(), key=lambda asset: asset.path)

    def list_assets_by_type(self, asset_type: str | AssetType) -> list[AssetInfo]:
        normalized = AssetType(str(asset_type))
        return [asset for asset in self.list_assets() if asset.type == normalized]

    def import_asset(self, path: str | Path) -> AssetInfo:
        absolute_path = self._absolute_asset_path(path)
        if absolute_path.suffix.lower() == ".meta":
            raise ValueError(".meta files are metadata, not primary assets")
        meta = self.ensure_meta(absolute_path)
        stat = absolute_path.stat()
        rel_path = self._relative_asset_path(absolute_path)
        info = AssetInfo(
            uuid=meta.uuid,
            name=absolute_path.stem,
            path=rel_path,
            absolute_path=absolute_path,
            type=meta.type,
            extension=absolute_path.suffix.lower(),
            size=int(stat.st_size),
            modified_time=float(stat.st_mtime),
            metadata_path=self._metadata_path(absolute_path),
        )
        self._assets_by_uuid[info.uuid] = info
        self._assets_by_path[info.path] = info
        return info

    def remove_missing_assets(self) -> int:
        removed = 0
        for meta_path in self.assets_root.rglob("*.meta"):
            source = meta_path.with_suffix("")
            if not source.exists():
                meta_path.unlink()
                removed += 1
        return removed

    def ensure_meta(self, asset_path: str | Path) -> AssetMeta:
        absolute_path = self._absolute_asset_path(asset_path)
        metadata_path = self._metadata_path(absolute_path)
        source_path = self._relative_asset_path(absolute_path)
        
        importer = self.importer_registry.get_importer_for(absolute_path)
        
        existing_meta = None
        if metadata_path.exists():
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                existing_meta = AssetMeta.from_dict(data)
            except Exception:
                pass

        meta = importer.import_asset(absolute_path, existing_meta)
        meta.source_path = source_path
        
        self._write_meta(metadata_path, meta)
        return meta

    def _iter_asset_files(self) -> Iterable[Path]:
        return (
            path
            for path in self.assets_root.rglob("*")
            if path.is_file()
            and path.suffix.lower() not in {".meta", ".pyc", ".pyo"}
            and "__pycache__" not in path.parts
        )

    def _metadata_path(self, asset_path: str | Path) -> Path:
        return Path(f"{self._absolute_asset_path(asset_path)}.meta")

    def _absolute_asset_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate.resolve()
        if candidate.parts and candidate.parts[0].lower() == "assets":
            return (self.project_root / candidate).resolve()
        return (self.assets_root / candidate).resolve()

    def _relative_asset_path(self, path: str | Path) -> str:
        absolute_path = self._absolute_asset_path(path)
        try:
            relative = absolute_path.relative_to(self.project_root)
        except ValueError:
            relative = absolute_path.relative_to(self.assets_root)
            return f"Assets/{relative.as_posix()}"
        return relative.as_posix()

    def _write_meta(self, path: Path, meta: AssetMeta) -> None:
        atomic_write_json(path, meta.to_dict())
