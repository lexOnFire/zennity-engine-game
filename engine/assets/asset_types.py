from __future__ import annotations

from enum import StrEnum
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
    return EXTENSION_TYPES.get(Path(path).suffix.lower(), AssetType.UNKNOWN)
