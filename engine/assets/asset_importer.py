from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List
import hashlib
import uuid

from engine.assets.asset_types import detect_asset_type
from engine.assets.asset_metadata import AssetMeta


class AssetImporter(ABC):
    """
    Base class for all asset importers.
    An importer is responsible for processing a source file and generating/updating its AssetMeta.
    """

    IMPORTER_VERSION = 1

    @classmethod
    @abstractmethod
    def get_importer_name(cls) -> str:
        """Returns a unique string identifying this importer (e.g. 'texture_importer')."""
        pass
        
    @classmethod
    @abstractmethod
    def get_supported_extensions(cls) -> List[str]:
        """Returns a list of file extensions supported by this importer (e.g. ['.png', '.jpg'])."""
        pass

    def import_asset(self, source_path: Path, existing_meta: AssetMeta | None = None) -> AssetMeta:
        """
        Imports the asset from source_path.
        If existing_meta is provided, it must preserve the UUID and merge import settings.
        Returns the updated or newly created AssetMeta.
        """
        asset_uuid = existing_meta.uuid if existing_meta else str(uuid.uuid4())
        asset_type = detect_asset_type(source_path)
        
        # Default settings if none exist
        import_settings = existing_meta.import_settings if existing_meta else {}
        dependencies = existing_meta.dependencies if existing_meta else []
        
        # Perform specific import logic via subclasses
        import_settings, dependencies = self.process_import(source_path, import_settings, dependencies)
        stat = source_path.stat() if source_path.exists() else None
        
        return AssetMeta(
            uuid=asset_uuid,
            type=asset_type,
            importer=self.get_importer_name(),
            source_path=source_path.as_posix(), # Normalizes paths
            import_settings=import_settings,
            dependencies=dependencies,
            importer_version=self.IMPORTER_VERSION,
            source_hash=_source_hash(source_path) if stat is not None else "",
            source_size=int(stat.st_size) if stat is not None else 0,
            source_modified_ns=int(stat.st_mtime_ns) if stat is not None else 0,
        )

    def needs_reimport(self, source_path: Path, meta: AssetMeta | None) -> bool:
        if meta is None:
            return True
        stat = source_path.stat()
        return (
            meta.importer != self.get_importer_name()
            or meta.importer_version != self.IMPORTER_VERSION
            or meta.source_size != int(stat.st_size)
            or meta.source_modified_ns != int(stat.st_mtime_ns)
        )

    def process_import(self, source_path: Path, import_settings: dict, dependencies: list) -> tuple[dict, list]:
        """
        Override this method in subclasses to add custom import settings or dependencies.
        Returns (updated_import_settings, updated_dependencies).
        """
        return import_settings, dependencies


class TextureImporter(AssetImporter):
    @classmethod
    def get_importer_name(cls) -> str:
        return "texture_importer"
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
        
    def process_import(self, source_path: Path, import_settings: dict, dependencies: list) -> tuple[dict, list]:
        if "filter_mode" not in import_settings:
            import_settings["filter_mode"] = "bilinear"
        return import_settings, dependencies


class AudioImporter(AssetImporter):
    @classmethod
    def get_importer_name(cls) -> str:
        return "audio_importer"
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return [".wav", ".mp3", ".ogg"]
        
    def process_import(self, source_path: Path, import_settings: dict, dependencies: list) -> tuple[dict, list]:
        if "load_type" not in import_settings:
            import_settings["load_type"] = "decompress_on_load"
        return import_settings, dependencies


class ScriptImporter(AssetImporter):
    @classmethod
    def get_importer_name(cls) -> str:
        return "script_importer"
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return [".py"]


class TilemapImporter(AssetImporter):
    @classmethod
    def get_importer_name(cls) -> str:
        return "tilemap_importer"
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return [".tmx", ".json"] # For potential external tilemap formats


class GenericImporter(AssetImporter):
    """Fallback importer for unknown file types."""
    @classmethod
    def get_importer_name(cls) -> str:
        return "generic_importer"
        
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        return ["*"]


class ImporterRegistry:
    """
    Central registry that maps file extensions to their respective AssetImporters.
    """
    def __init__(self):
        self._importers_by_ext: Dict[str, AssetImporter] = {}
        self._fallback_importer = GenericImporter()
        
        self.register_importer(TextureImporter())
        self.register_importer(AudioImporter())
        self.register_importer(ScriptImporter())
        self.register_importer(TilemapImporter())
        
    def register_importer(self, importer: AssetImporter) -> None:
        for ext in importer.get_supported_extensions():
            self._importers_by_ext[ext.lower()] = importer
            
    def get_importer_for(self, path: str | Path) -> AssetImporter:
        if isinstance(path, str):
            path = Path(path)
        ext = path.suffix.lower()
        return self._importers_by_ext.get(ext, self._fallback_importer)


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
