from pathlib import Path

from engine.assets.reference import AssetReference


class _Info:
    absolute_path = Path("Assets/Textures/player.png")


class _Database:
    def get_asset_by_uuid(self, value): return _Info() if value == "guid" else None
    def get_asset_by_path(self, value): return _Info() if value.endswith("player.png") else None


def test_asset_reference_prefers_guid_and_serializes_fallback():
    reference = AssetReference("guid", "Assets/Textures/old.png")
    assert reference.resolve(_Database()) == Path("Assets/Textures/player.png")
    assert reference.to_dict() == {"guid": "guid", "path": "Assets/Textures/old.png"}


def test_asset_reference_accepts_legacy_path():
    reference = AssetReference.from_value("Assets/Textures/player.png")
    assert reference.guid == ""
    assert reference.resolve(_Database()) == Path("Assets/Textures/player.png")
