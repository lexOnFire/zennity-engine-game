from __future__ import annotations

from pathlib import Path

from engine.assets.asset_types import AssetType, detect_asset_type


IMPORTERS: dict[AssetType, str] = {
    AssetType.SCENE: "scene_importer",
    AssetType.IMAGE: "image_importer",
    AssetType.AUDIO: "audio_importer",
    AssetType.SCRIPT: "script_importer",
    AssetType.FONT: "font_importer",
    AssetType.MATERIAL: "material_importer",
    AssetType.PREFAB: "prefab_importer",
    AssetType.UNKNOWN: "generic_importer",
}


class AssetImporter:
    """Classifies project files for the Asset Database."""

    def detect_type(self, path: str | Path) -> AssetType:
        return detect_asset_type(path)

    def importer_for(self, asset_type: AssetType) -> str:
        return IMPORTERS.get(asset_type, IMPORTERS[AssetType.UNKNOWN])

    def import_asset(self, path: str | Path) -> tuple[AssetType, str]:
        asset_type = self.detect_type(path)
        return asset_type, self.importer_for(asset_type)
