from __future__ import annotations

import json
from types import SimpleNamespace

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
