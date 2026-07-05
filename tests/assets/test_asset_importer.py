from __future__ import annotations

from engine.assets import AssetImporter, AssetType


def test_asset_importer_recognizes_supported_types() -> None:
    importer = AssetImporter()

    assert importer.import_asset("level.zscene") == (AssetType.SCENE, "scene_importer")
    assert importer.import_asset("texture.png") == (AssetType.IMAGE, "image_importer")
    assert importer.import_asset("texture.jpg") == (AssetType.IMAGE, "image_importer")
    assert importer.import_asset("music.ogg") == (AssetType.AUDIO, "audio_importer")
    assert importer.import_asset("code.py") == (AssetType.SCRIPT, "script_importer")
    assert importer.import_asset("font.ttf") == (AssetType.FONT, "font_importer")
    assert importer.import_asset("mat.zmat") == (AssetType.MATERIAL, "material_importer")
    assert importer.import_asset("prefab.zprefab") == (AssetType.PREFAB, "prefab_importer")


def test_asset_importer_unknown_type() -> None:
    importer = AssetImporter()

    assert importer.import_asset("notes.txt") == (AssetType.UNKNOWN, "generic_importer")
