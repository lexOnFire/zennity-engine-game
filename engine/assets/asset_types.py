from __future__ import annotations

try:
    from enum import StrEnum
except ImportError:  # Python 3.10
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)
from pathlib import Path


class AssetType(StrEnum):
    SCENE = "scene"
    IMAGE = "image"
    AUDIO = "audio"
    SCRIPT = "script"
    FONT = "font"
    MATERIAL = "material"
    PREFAB = "prefab"
    UNKNOWN = "unknown"


EXTENSION_TYPES: dict[str, AssetType] = {
    ".zscene": AssetType.SCENE,
    ".png": AssetType.IMAGE,
    ".jpg": AssetType.IMAGE,
    ".jpeg": AssetType.IMAGE,
    ".bmp": AssetType.IMAGE,
    ".wav": AssetType.AUDIO,
    ".ogg": AssetType.AUDIO,
    ".mp3": AssetType.AUDIO,
    ".py": AssetType.SCRIPT,
    ".ttf": AssetType.FONT,
    ".otf": AssetType.FONT,
    ".zmat": AssetType.MATERIAL,
    ".zprefab": AssetType.PREFAB,
}


def detect_asset_type(path: str | Path) -> AssetType:
    suffix = Path(path).suffix.lower()
    
    # Try dynamic metadata first
    from engine.core.context import EngineContext
    context = EngineContext.current()
    if context:
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata import AssetTypeDefinition
        manager = context.services.get_optional(MetadataManager)
        if manager:
            # Query all AssetTypeDefinitions and see which one has the extension
            definitions = manager.get_all(AssetTypeDefinition)
            for d in definitions:
                if suffix in getattr(d, "extensions", []):
                    # We map definition ID back to AssetType enum if possible, or create a new enum entry
                    # Assuming id matches the enum value string
                    try:
                        return AssetType(d.id)
                    except ValueError:
                        # Fallback for dynamic types not in Enum
                        pass
    
    # Fallback to static mapping
    return EXTENSION_TYPES.get(suffix, AssetType.UNKNOWN)
