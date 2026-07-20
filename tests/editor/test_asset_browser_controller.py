from pathlib import Path
from types import SimpleNamespace

from editor.asset_browser_controller import AssetBrowserController


def test_asset_root_prefers_canonical_case_and_supports_legacy_case(tmp_path: Path) -> None:
    legacy_root = tmp_path / "legacy_project"
    legacy_root.mkdir()
    legacy = legacy_root / "assets"
    legacy.mkdir()
    legacy_controller = AssetBrowserController(
        SimpleNamespace(), legacy_root, SimpleNamespace(),
    )
    assert legacy_controller.asset_root() == legacy

    canonical_root = tmp_path / "canonical_project"
    canonical_root.mkdir()
    canonical = canonical_root / "Assets"
    canonical.mkdir()
    canonical_controller = AssetBrowserController(
        SimpleNamespace(), canonical_root, SimpleNamespace(),
    )
    assert canonical_controller.asset_root() == canonical


def test_asset_classification_hides_internal_files_and_assigns_icons(tmp_path: Path) -> None:
    script = tmp_path / "player.py"
    animation = tmp_path / "walk.zanim"
    image = tmp_path / "hero.png"
    for path in (script, animation, image):
        path.touch()

    assert AssetBrowserController._hidden(script)
    assert AssetBrowserController.asset_icon(animation) == "🎞 "
    assert AssetBrowserController.asset_icon(image) == "🖼️ "
