from pathlib import Path

from engine.assets.asset_importer import (
    ImporterRegistry,
    TextureImporter,
    AudioImporter,
    ScriptImporter,
    GenericImporter,
)
from engine.assets.asset_metadata import AssetMeta
from engine.assets.asset_types import AssetType

def test_importer_registry_resolves_correctly():
    registry = ImporterRegistry()
    
    assert isinstance(registry.get_importer_for("image.png"), TextureImporter)
    assert isinstance(registry.get_importer_for("sound.wav"), AudioImporter)
    assert isinstance(registry.get_importer_for("logic.py"), ScriptImporter)
    assert isinstance(registry.get_importer_for("unknown.xyz"), GenericImporter)


def test_texture_importer_creates_meta():
    importer = TextureImporter()
    path = Path("Assets/Textures/player.png")
    
    meta = importer.import_asset(path)
    
    assert meta.type == AssetType.IMAGE
    assert meta.importer == "texture_importer"
    assert meta.uuid is not None
    assert meta.source_path == "Assets/Textures/player.png"
    assert "filter_mode" in meta.import_settings
    assert meta.import_settings["filter_mode"] == "bilinear"


def test_importer_preserves_uuid_and_updates_settings():
    importer = TextureImporter()
    path = Path("Assets/Textures/player.png")
    
    existing_meta = AssetMeta(
        uuid="test-uuid-1234",
        type=AssetType.IMAGE,
        importer="texture_importer",
        source_path="Assets/Textures/old_player.png",
        import_settings={"custom_setting": True}
    )
    
    meta = importer.import_asset(path, existing_meta)
    
    assert meta.uuid == "test-uuid-1234" # Preserved
    assert meta.type == AssetType.IMAGE
    assert meta.source_path == "Assets/Textures/player.png" # Updated
    assert "filter_mode" in meta.import_settings
    assert meta.import_settings["custom_setting"] is True # Preserved
    
def test_audio_importer_creates_meta():
    importer = AudioImporter()
    path = Path("Assets/Audio/music.ogg")
    
    meta = importer.import_asset(path)
    
    assert meta.type == AssetType.AUDIO
    assert meta.importer == "audio_importer"
    assert meta.import_settings["load_type"] == "decompress_on_load"

