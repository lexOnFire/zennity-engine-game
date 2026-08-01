from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from engine.assets import AssetDatabase, AssetPathResolver


def _write(path: Path, data: bytes = b"asset") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_resolver_canonicalizes_assets_root_spelling(tmp_path: Path) -> None:
    resolver = AssetPathResolver(tmp_path)

    assert resolver.canonicalize("assets/scripts/player.py") == "Assets/scripts/player.py"
    assert resolver.canonicalize("ASSETS\\Textures\\hero.png") == "Assets/Textures/hero.png"


def test_database_scans_canonical_and_legacy_asset_roots(tmp_path: Path) -> None:
    _write(tmp_path / "Assets" / "Textures" / "hero.png")
    legacy = _write(tmp_path / "assets" / "scripts" / "legacy.py")
    database = AssetDatabase(tmp_path)

    assets = database.scan()

    assert {asset.path for asset in assets} == {
        "Assets/Textures/hero.png",
        "Assets/scripts/legacy.py",
    }
    assert database.get_asset_by_path("ASSETS/SCRIPTS/LEGACY.PY").absolute_path == legacy


@pytest.mark.skipif(
    os.path.normcase("Assets") == os.path.normcase("assets"),
    reason="Requires a case-sensitive filesystem with distinct Assets and assets trees",
)
def test_canonical_tree_wins_case_insensitive_path_collision(tmp_path: Path) -> None:
    canonical = _write(tmp_path / "Assets" / "Scripts" / "player.py", b"canonical")
    legacy = _write(tmp_path / "assets" / "scripts" / "PLAYER.py", b"legacy")
    database = AssetDatabase(tmp_path)

    assets = database.scan()

    assert len(assets) == 1
    assert assets[0].absolute_path == canonical
    assert database.path_conflicts == [("Assets/scripts/PLAYER.py", canonical, legacy)]


def test_duplicate_guid_is_repaired_without_changing_first_asset(tmp_path: Path) -> None:
    first = _write(tmp_path / "Assets" / "first.png")
    second = _write(tmp_path / "Assets" / "second.png")
    shared = "shared-guid"
    for path in (first, second):
        Path(f"{path}.meta").write_text(
            json.dumps({"uuid": shared, "type": "image", "importer": "texture_importer"}),
            encoding="utf-8",
        )
    database = AssetDatabase(tmp_path)

    assets = database.scan()

    assert len({asset.guid for asset in assets}) == 2
    assert len(database.guid_conflicts) == 1
    assert database.get_asset_by_guid(shared) is not None


def test_metadata_migrates_legacy_uuid_to_canonical_guid(tmp_path: Path) -> None:
    asset = _write(tmp_path / "Assets" / "player.png")
    meta_path = Path(f"{asset}.meta")
    meta_path.write_text(
        json.dumps({"uuid": "legacy-id", "type": "image", "importer": "texture_importer"}),
        encoding="utf-8",
    )

    info = AssetDatabase(tmp_path).scan()[0]
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    assert info.guid == "legacy-id"
    assert metadata["guid"] == "legacy-id"
    assert metadata["uuid"] == "legacy-id"
