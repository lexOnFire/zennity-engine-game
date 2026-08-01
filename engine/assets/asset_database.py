from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Iterable

from engine.core.services import IService
from engine.core.lifecycle import ServiceScope, ServiceState
from engine.assets.asset_handle import AssetHandle
from engine.assets.asset_importer import ImporterRegistry
from engine.assets.asset_metadata import AssetInfo, AssetMeta
from engine.assets.asset_path import AssetPathResolver
from engine.assets.asset_types import AssetType


class AssetDatabase(IService):
    """Scans the project Assets directory and maintains .meta files as a Core Service."""

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
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.path_resolver = AssetPathResolver(self.project_root)
        self.assets_root = (self.project_root / assets_dir).resolve()
        self.importer_registry = ImporterRegistry()
        self._assets_by_uuid: dict[str, AssetInfo] = {}
        self._assets_by_path: dict[str, AssetInfo] = {}
        self.path_conflicts: list[tuple[str, Path, Path]] = []
        self.guid_conflicts: list[tuple[str, Path, Path]] = []

    def initialize(self) -> None:
        """Chamado quando o serviço é inicializado no contexto do Engine Core."""
        self.scan()

    def shutdown(self) -> None:
        """Chamado no desativamento do serviço."""
        self._assets_by_uuid.clear()
        self._assets_by_path.clear()
        self.path_conflicts.clear()
        self.guid_conflicts.clear()

    def scan(self) -> list[AssetInfo]:
        self.ensure_project_folders()
        self._assets_by_uuid.clear()
        self._assets_by_path.clear()
        self.path_conflicts.clear()
        self.guid_conflicts.clear()

        for path in self._iter_asset_files():
            info = self.import_asset(path)

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

    def get_asset_by_guid(self, asset_guid: str) -> AssetInfo | None:
        return self._assets_by_uuid.get(str(asset_guid))

    def get_asset_by_handle(self, handle: AssetHandle | str) -> AssetInfo | None:
        if isinstance(handle, AssetHandle):
            return self.get_asset_by_guid(handle.guid)
        if not handle:
            return None
        # Try GUID lookup first, fallback to path lookup
        asset = self.get_asset_by_guid(str(handle))
        if asset is not None:
            return asset
        return self.get_asset_by_path(str(handle))

    def resolve_handle(self, path: str | Path) -> AssetHandle | None:
        asset = self.get_asset_by_path(path)
        if asset is not None:
            return AssetHandle(asset.uuid)
        return None

    def resolve_path(self, handle: AssetHandle | str) -> Path | None:
        asset = self.get_asset_by_handle(handle)
        return asset.absolute_path if asset is not None else None

    def get_asset_by_path(self, path: str | Path) -> AssetInfo | None:
        return self._assets_by_path.get(self.path_resolver.lookup_key(path))

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
        existing_guid = self._assets_by_uuid.get(info.guid)
        if existing_guid is not None and existing_guid.absolute_path != info.absolute_path:
            self.guid_conflicts.append((info.guid, existing_guid.absolute_path, info.absolute_path))
            meta.uuid = str(uuid.uuid4())
            self._write_meta(info.metadata_path, meta)
            info = AssetInfo(
                uuid=meta.guid,
                name=info.name,
                path=info.path,
                absolute_path=info.absolute_path,
                type=info.type,
                extension=info.extension,
                size=info.size,
                modified_time=info.modified_time,
                metadata_path=info.metadata_path,
            )
        self._assets_by_uuid[info.uuid] = info
        self._assets_by_path[self.path_resolver.lookup_key(info.path)] = info
        return info

    def remove_missing_assets(self) -> int:
        removed = 0
        for root in self.path_resolver.physical_roots():
            if not root.exists():
                continue
            for meta_path in root.rglob("*.meta"):
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
        selected: dict[str, Path] = {}
        for root in self.path_resolver.physical_roots():
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() in {".meta", ".bak", ".tmp"} or path.name.startswith("."):
                    continue
                canonical = self.path_resolver.canonicalize(path)
                key = canonical.casefold()
                existing = selected.get(key)
                if existing is not None:
                    self.path_conflicts.append((canonical, existing, path))
                    continue
                selected[key] = path
        return iter(selected.values())

    def _metadata_path(self, asset_path: str | Path) -> Path:
        return Path(f"{self._absolute_asset_path(asset_path)}.meta")

    def _absolute_asset_path(self, path: str | Path) -> Path:
        return self.path_resolver.resolve(path)

    def _relative_asset_path(self, path: str | Path) -> str:
        return self.path_resolver.canonicalize(self._absolute_asset_path(path))

    def _write_meta(self, path: Path, meta: AssetMeta) -> None:
        serialized = json.dumps(meta.to_dict(), indent=2, ensure_ascii=False) + "\n"
        if path.exists():
            try:
                if path.read_text(encoding="utf-8") == serialized:
                    return
            except (OSError, UnicodeError):
                pass
        temporary_path = path.with_name(
            f".{path.name}.{uuid.uuid4().hex}.tmp"
        )
        try:
            temporary_path.write_text(serialized, encoding="utf-8", newline="\n")
            temporary_path.replace(path)
        except PermissionError:
            pass
        finally:
            temporary_path.unlink(missing_ok=True)
