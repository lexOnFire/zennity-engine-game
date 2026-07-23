from pathlib import Path

from engine.assets import AssetPathResolver


def test_repository_has_only_canonical_root_assets_tree() -> None:
    root_names = {path.name for path in Path.cwd().iterdir() if path.is_dir()}
    assert "Assets" in root_names
    assert "assets" not in root_names


def test_external_legacy_projects_remain_resolvable(tmp_path) -> None:
    legacy = tmp_path / "assets" / "scripts" / "player.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("def start(game): pass\n", encoding="utf-8")

    resolver = AssetPathResolver(tmp_path)

    assert resolver.canonicalize(legacy) == "Assets/scripts/player.py"
    assert resolver.resolve("Assets/Scripts/Player.py", must_exist=True) == legacy.resolve()
