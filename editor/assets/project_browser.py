from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from engine.assets import AssetDatabase, AssetInfo
from engine.assets.asset_types import AssetType, detect_asset_type


THUMBNAIL_BY_TYPE = {
    AssetType.IMAGE: "thumbnail:image",
    AssetType.SCENE: "thumbnail:scene",
    AssetType.PREFAB: "thumbnail:prefab",
}


def thumbnail_key_for(path: str | Path, asset_type: AssetType | str | None = None) -> str:
    path = Path(path)
    detected = AssetType(str(asset_type)) if asset_type is not None else detect_asset_type(path)
    if path.suffix.lower() in {".tmx", ".json"}:
        return "thumbnail:tilemap"
    return THUMBNAIL_BY_TYPE.get(detected, "thumbnail:default")


@dataclass
class ProjectBrowserSession:
    view_mode: str = "grid"
    favorite_folders: set[str] = field(default_factory=set)

    def set_view_mode(self, mode: str) -> None:
        if mode not in {"list", "grid"}:
            raise ValueError("Project Browser view mode must be 'list' or 'grid'")
        self.view_mode = mode

    def add_favorite(self, path: str) -> None:
        self.favorite_folders.add(_normalize_rel_path(path))

    def remove_favorite(self, path: str) -> None:
        self.favorite_folders.discard(_normalize_rel_path(path))

    def is_favorite(self, path: str) -> bool:
        return _normalize_rel_path(path) in self.favorite_folders

    def list_favorites(self) -> list[str]:
        return sorted(self.favorite_folders)


class ProjectBrowserService:
    """Editor-only file operations for the Project Browser."""

    def __init__(self, database: AssetDatabase | None = None, session: ProjectBrowserSession | None = None) -> None:
        self.database = database or AssetDatabase()
        self.session = session or ProjectBrowserSession()
        self.database.ensure_project_folders()

    @property
    def assets_root(self) -> Path:
        return self.database.assets_root

    def refresh(self) -> list[AssetInfo]:
        return self.database.refresh()

    def reimport_asset(self, asset: str | Path) -> AssetInfo:
        """Force an asset import and refresh the derived project index."""
        return self.database.reimport_asset(self._asset_path(asset))

    def search_assets(self, query: str) -> list[AssetInfo]:
        query = query.strip().lower()
        if not query:
            return self.database.list_assets()
        matches: list[AssetInfo] = []
        for asset in self.database.list_assets():
            fields = [
                asset.name,
                asset.extension,
                asset.type.value,
                asset.path,
            ]
            if any(query in str(field).lower() for field in fields):
                matches.append(asset)
        return matches

    def create_folder(self, parent: str | Path = "Assets", name: str = "New Folder") -> Path:
        parent_path = self._asset_path(parent)
        parent_path.mkdir(parents=True, exist_ok=True)
        folder = _unique_path(parent_path / _safe_name(name, fallback="New Folder"))
        folder.mkdir()
        self.refresh()
        return folder

    def rename_asset(self, asset: str | Path, new_name: str) -> Path:
        source = self._asset_path(asset)
        if not source.exists():
            raise FileNotFoundError(source)
        clean = _safe_name(new_name, fallback=source.stem)
        destination = source.with_name(clean if source.is_dir() else f"{Path(clean).stem}{source.suffix}")
        destination = _unique_path(destination)
        source.rename(destination)
        self._move_meta(source, destination)
        self.refresh()
        return destination

    def duplicate_asset(self, asset: str | Path) -> Path:
        source = self._asset_path(asset)
        if not source.exists():
            raise FileNotFoundError(source)
        destination = _unique_path(source.with_name(f"{source.stem}_copy{source.suffix}"))
        if source.is_dir():
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns("*.meta"))
        else:
            shutil.copy2(source, destination)
        self.refresh()
        return destination

    def delete_asset(self, asset: str | Path) -> None:
        source = self._asset_path(asset)
        if source.is_dir():
            shutil.rmtree(source)
        elif source.exists():
            source.unlink()
        meta = self._meta_path(source)
        if meta.exists():
            meta.unlink()
        self.refresh()

    def move_asset(self, asset: str | Path, folder: str | Path) -> Path:
        source = self._asset_path(asset)
        target_folder = self._asset_path(folder)
        if not source.exists():
            raise FileNotFoundError(source)
        target_folder.mkdir(parents=True, exist_ok=True)
        destination = _unique_path(target_folder / source.name)
        shutil.move(str(source), str(destination))
        self._move_meta(source, destination)
        self.refresh()
        return destination

    def copy_path(self, asset: str | Path) -> str:
        return self._relative_path(self._asset_path(asset))

    def reveal_path(self, asset: str | Path) -> Path:
        return self._asset_path(asset)

    def thumbnail_for_asset(self, asset: AssetInfo) -> str:
        return thumbnail_key_for(asset.path, asset.type)

    def _asset_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        elif candidate.parts and candidate.parts[0].lower() == "assets":
            resolved = (self.database.project_root / candidate).resolve()
        else:
            resolved = (self.assets_root / candidate).resolve()
        if self.assets_root not in resolved.parents and resolved != self.assets_root:
            raise ValueError("Project Browser operations are limited to Assets/")
        return resolved

    def _relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.database.project_root).as_posix()

    def _meta_path(self, path: Path) -> Path:
        return Path(f"{path}.meta")

    def _move_meta(self, old_path: Path, new_path: Path) -> None:
        old_meta = self._meta_path(old_path)
        if old_meta.exists():
            new_meta = self._meta_path(new_path)
            new_meta.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_meta), str(new_meta))


def _safe_name(value: str, fallback: str) -> str:
    value = str(value).strip()
    if not value:
        return fallback
    return value.replace("/", "_").replace("\\", "_")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    if path.is_dir() or not path.suffix:
        stem = path.name
        suffix = ""
    else:
        stem = path.stem
        suffix = path.suffix
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _normalize_rel_path(path: str) -> str:
    return Path(str(path)).as_posix().rstrip("/")
