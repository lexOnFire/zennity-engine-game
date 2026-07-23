from __future__ import annotations

from pathlib import Path

from editor.assets.project_browser import (
    ProjectBrowserService,
    ProjectBrowserSession,
    thumbnail_key_for,
)
from engine.assets import AssetDatabase


def _write_asset(root: Path, relative: str, data: bytes = b"asset") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_project_browser_thumbnail_keys() -> None:
    assert thumbnail_key_for("Assets/Textures/player.png") == "thumbnail:image"
    assert thumbnail_key_for("Assets/Scenes/main.zscene") == "thumbnail:scene"
    assert thumbnail_key_for("Assets/Prefabs/player.zprefab") == "thumbnail:prefab"
    assert thumbnail_key_for("Assets/Tilemaps/level.tmx") == "thumbnail:tilemap"
    assert thumbnail_key_for("Assets/Data/readme.txt") == "thumbnail:default"


def test_project_browser_search_by_name_extension_and_type(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/hero.png")
    _write_asset(tmp_path, "Assets/Scripts/player_controller.py", b"print('ok')")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    service.refresh()

    assert [asset.name for asset in service.search_assets("hero")] == ["hero"]
    assert [asset.name for asset in service.search_assets(".py")] == ["player_controller"]
    assert [asset.name for asset in service.search_assets("script")] == ["player_controller"]


def test_project_browser_rename_preserves_guid_and_refreshes_database(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/player.png")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    service.refresh()
    original = database.get_asset_by_path("Assets/Textures/player.png")
    assert original is not None

    renamed = service.rename_asset("Assets/Textures/player.png", "hero")
    updated = database.get_asset_by_path("Assets/Textures/hero.png")

    assert renamed.name == "hero.png"
    assert updated is not None
    assert updated.uuid == original.uuid
    assert not (tmp_path / "Assets/Textures/player.png.meta").exists()
    assert (tmp_path / "Assets/Textures/hero.png.meta").exists()


def test_project_browser_move_preserves_guid_and_refreshes_database(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/player.png")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    service.refresh()
    original = database.get_asset_by_path("Assets/Textures/player.png")
    assert original is not None

    moved = service.move_asset("Assets/Textures/player.png", "Assets/Prefabs")
    updated = database.get_asset_by_path("Assets/Prefabs/player.png")

    assert moved == tmp_path / "Assets/Prefabs/player.png"
    assert updated is not None
    assert updated.uuid == original.uuid
    assert (tmp_path / "Assets/Prefabs/player.png.meta").exists()


def test_project_browser_duplicate_creates_new_guid(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/player.png")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    service.refresh()
    original = database.get_asset_by_path("Assets/Textures/player.png")
    assert original is not None

    duplicate = service.duplicate_asset("Assets/Textures/player.png")
    service.refresh()
    copied = database.get_asset_by_path("Assets/Textures/player_copy.png")

    assert duplicate == tmp_path / "Assets/Textures/player_copy.png"
    assert copied is not None
    assert copied.uuid != original.uuid


def test_project_browser_delete_removes_asset_and_meta(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/player.png")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    service.refresh()

    service.delete_asset("Assets/Textures/player.png")

    assert database.get_asset_by_path("Assets/Textures/player.png") is None
    assert not (tmp_path / "Assets/Textures/player.png").exists()
    assert not (tmp_path / "Assets/Textures/player.png.meta").exists()


def test_project_browser_create_folder_uses_unique_name(tmp_path: Path) -> None:
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)

    first = service.create_folder("Assets", "Sprites")
    second = service.create_folder("Assets", "Sprites")

    assert first.name == "Sprites"
    assert second.name == "Sprites_1"
    assert first.is_dir()
    assert second.is_dir()


def test_project_browser_session_tracks_view_mode_and_favorites() -> None:
    session = ProjectBrowserSession()

    session.set_view_mode("list")
    session.add_favorite("Assets/Textures/")
    session.add_favorite("Assets/Scripts")
    session.remove_favorite("Assets/Scripts")

    assert session.view_mode == "list"
    assert session.is_favorite("Assets/Textures")
    assert session.list_favorites() == ["Assets/Textures"]


def test_project_browser_can_force_asset_reimport(tmp_path: Path) -> None:
    _write_asset(tmp_path, "Assets/Textures/player.png", b"texture")
    database = AssetDatabase(tmp_path)
    service = ProjectBrowserService(database)
    original = service.refresh()[0]

    reimported = service.reimport_asset(original.path)

    assert reimported.guid == original.guid
    assert database.last_scan_imported == 1
    assert database.cache.load()[original.guid]["path"] == original.path


def test_resources_panel_exposes_reimport_action() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "editor"
        / "premium_resources_panel.py"
    ).read_text(encoding="utf-8")

    assert 'menu.addAction("Reimport")' in source
    assert "self.browser.reimport_asset(path)" in source
