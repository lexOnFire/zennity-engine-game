from __future__ import annotations

from engine.assets.asset_importer import ImporterRegistry


def test_asset_importer_recognizes_supported_types() -> None:
    registry = ImporterRegistry()

    assert registry.get_importer_for("texture.png").get_importer_name() == "texture_importer"
    assert registry.get_importer_for("texture.jpg").get_importer_name() == "texture_importer"
    assert registry.get_importer_for("music.ogg").get_importer_name() == "audio_importer"
    assert registry.get_importer_for("code.py").get_importer_name() == "script_importer"


def test_asset_importer_unknown_type() -> None:
    registry = ImporterRegistry()

    assert registry.get_importer_for("notes.txt").get_importer_name() == "generic_importer"
