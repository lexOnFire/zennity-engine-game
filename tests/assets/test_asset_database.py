from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.assets import AssetDatabase, AssetType
from engine.game_object import GameObject
from engine.scene import serialize_scene


def _write(path, data: bytes = b"data"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_scan_creates_assets_folder(tmp_path) -> None:
    db = AssetDatabase(tmp_path)

    assets = db.scan()

    assert assets == []
    assert (tmp_path / "Assets").is_dir()
    for folder in AssetDatabase.DEFAULT_FOLDERS:
        assert (tmp_path / "Assets" / folder).is_dir()


def test_scan_recognizes_types_and_creates_meta(tmp_path) -> None:
    _write(tmp_path / "Assets" / "Scenes" / "main.zscene", b"{}")
    _write(tmp_path / "Assets" / "Textures" / "player.png")
    _write(tmp_path / "Assets" / "Scripts" / "player.py")
    db = AssetDatabase(tmp_path)

    assets = db.scan()

    assert {asset.type for asset in assets} == {AssetType.SCENE, AssetType.IMAGE, AssetType.SCRIPT}
    for asset in assets:
        assert asset.metadata_path.exists()
        meta = json.loads(asset.metadata_path.read_text(encoding="utf-8"))
        assert meta["uuid"] == asset.uuid
        assert meta["type"] == asset.type.value
        assert meta["source_path"] == asset.path


def test_meta_uuid_is_stable_across_refresh(tmp_path) -> None:
    texture = _write(tmp_path / "Assets" / "player.png")
    db = AssetDatabase(tmp_path)

    first = db.scan()[0].uuid
    texture.write_bytes(b"updated")
    second = db.refresh()[0].uuid

    assert second == first


def test_atomic_meta_write_preserves_original_when_replace_fails(
    tmp_path, monkeypatch,
) -> None:
    asset_path = _write(tmp_path / "Assets" / "Scripts" / "rotate.py")
    db = AssetDatabase(tmp_path)
    meta = db.ensure_meta(asset_path)
    meta_path = Path(f"{asset_path}.meta")
    original = meta_path.read_text(encoding="utf-8")
    meta.import_settings["changed"] = True

    def fail_replace(_source: Path, _target: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        db._write_meta(meta_path, meta)

    assert meta_path.read_text(encoding="utf-8") == original
    assert list(meta_path.parent.glob(f".{meta_path.name}.*.tmp")) == []


def test_list_assets_by_type_and_lookup(tmp_path) -> None:
    _write(tmp_path / "Assets" / "player.png")
    _write(tmp_path / "Assets" / "jump.wav")
    db = AssetDatabase(tmp_path)
    db.scan()

    images = db.list_assets_by_type(AssetType.IMAGE)
    image = images[0]

    assert len(images) == 1
    assert db.get_asset_by_uuid(image.uuid) is image
    assert db.get_asset_by_path("Assets/player.png") is image
    assert db.get_asset_by_path("player.png") is image


def test_scan_ignores_meta_as_primary_asset(tmp_path) -> None:
    _write(tmp_path / "Assets" / "player.png")
    _write(tmp_path / "Assets" / "orphan.txt.meta", b"{}")
    db = AssetDatabase(tmp_path)

    assets = db.scan()

    assert [asset.path for asset in assets] == ["Assets/player.png"]


def test_remove_missing_assets_deletes_orphan_meta(tmp_path) -> None:
    asset = _write(tmp_path / "Assets" / "player.png")
    db = AssetDatabase(tmp_path)
    meta_path = db.scan()[0].metadata_path
    asset.unlink()

    removed = db.remove_missing_assets()

    assert removed == 1
    assert not meta_path.exists()


def test_asset_paths_are_project_relative(tmp_path) -> None:
    _write(tmp_path / "Assets" / "Nested" / "font.ttf")
    db = AssetDatabase(tmp_path)

    asset = db.scan()[0]

    assert asset.path == "Assets/Nested/font.ttf"
    assert asset.absolute_path == tmp_path / "Assets" / "Nested" / "font.ttf"
    assert asset.metadata_path == tmp_path / "Assets" / "Nested" / "font.ttf.meta"


def test_zscene_uses_relative_asset_reference(tmp_path) -> None:
    sprite = _write(tmp_path / "Assets" / "Textures" / "player.png")
    db = AssetDatabase(tmp_path)
    asset = db.scan()[0]
    obj = GameObject("Player")
    obj.sprite_path = asset.path
    obj.asset_uuid = asset.uuid
    scene = SimpleNamespace(name="Level", editable_objects=[obj])

    data = serialize_scene(scene)
    visual = data["objects"][0]["visual"]

    assert visual["sprite_path"] == "Assets/Textures/player.png"
    assert visual["asset_uuid"] == asset.uuid
    assert str(sprite) not in json.dumps(data)


def test_unchanged_scan_reuses_metadata_without_reimport(tmp_path) -> None:
    _write(tmp_path / "Assets" / "Textures" / "player.png", b"original")
    db = AssetDatabase(tmp_path)

    first = db.scan()[0]
    first_meta = db.get_metadata(first.guid)
    second = db.scan()[0]

    assert second.guid == first.guid
    assert db.last_scan_imported == 0
    assert db.last_scan_reused == 1
    assert db.get_metadata(second.guid) == first_meta


def test_changed_source_reimports_with_stable_guid_and_new_hash(tmp_path) -> None:
    source = _write(tmp_path / "Assets" / "Textures" / "player.png", b"one")
    db = AssetDatabase(tmp_path)
    first = db.scan()[0]
    original_hash = db.get_metadata(first.guid).source_hash

    source.write_bytes(b"updated-content")
    second = db.scan()[0]
    updated_meta = db.get_metadata(second.guid)

    assert second.guid == first.guid
    assert db.last_scan_imported == 1
    assert updated_meta.source_hash != original_hash
    assert updated_meta.source_size == len(b"updated-content")


def test_force_reimport_preserves_guid_and_updates_cache(tmp_path) -> None:
    source = _write(tmp_path / "Assets" / "Audio" / "theme.ogg", b"audio")
    db = AssetDatabase(tmp_path)
    original = db.scan()[0]
    cache_before = db.cache.index_path.read_text(encoding="utf-8")

    reimported = db.reimport_asset(source)
    cache_after = json.loads(db.cache.index_path.read_text(encoding="utf-8"))

    assert reimported.guid == original.guid
    assert db.last_scan_imported == 1
    assert cache_before
    assert cache_after["assets"][original.guid]["path"] == original.path


def test_cache_is_derived_and_rebuilt_after_corruption(tmp_path) -> None:
    _write(tmp_path / "Assets" / "Scripts" / "player.py", b"print('ok')")
    db = AssetDatabase(tmp_path)
    asset = db.scan()[0]
    db.cache.index_path.write_text("{broken", encoding="utf-8")

    assert db.cache.load() == {}

    db.scan()
    cached = db.cache.load()

    assert cached[asset.guid]["path"] == "Assets/Scripts/player.py"
    assert cached[asset.guid]["source_hash"]
