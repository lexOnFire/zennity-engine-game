from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type
import uuid

from engine.assets.asset_types import AssetType, detect_asset_type
from engine.assets.asset_metadata import AssetMeta, compute_file_hash


class AssetImporter(ABC):
    """
    Base class for all asset importers.
    An importer is responsible for processing a source file and generating/updating its AssetMeta.
    """
    
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
        file_hash = compute_file_hash(source_path)
        
        # Perform specific import logic via subclasses
        import_settings, dependencies = self.process_import(source_path, import_settings, dependencies)
        
        return AssetMeta(
            uuid=asset_uuid,
            type=asset_type,
            importer=self.get_importer_name(),
            source_path=source_path.as_posix(), # Normalizes paths
            import_settings=import_settings,
            dependencies=dependencies,
            hash=file_hash,
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
    Now wraps the Engine's MetadataManager.
    """
    def __init__(self):
        self._fallback_importer = GenericImporter()
        self._importers: Dict[str, AssetImporter] = {}
        self.register(TextureImporter())
        self.register(AudioImporter())
        self.register(ScriptImporter())
        self.register(TilemapImporter())
        
    def register(self, importer: AssetImporter) -> None:
        for ext in importer.get_supported_extensions():
            self._importers[ext] = importer
            
    def get_importer_for(self, path: str | Path) -> AssetImporter:
        if isinstance(path, str):
            path = Path(path)
        ext = path.suffix.lower()
        
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata import ImporterDefinition
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                # Find all importers that support this extension
                defs = manager.get_all(ImporterDefinition)
                for d in defs:
                    if ext in d.extensions and d.importer_class:
                        return d.importer_class()
                        
        if ext in self._importers:
            return self._importers[ext]
            
        return self._fallback_importer
