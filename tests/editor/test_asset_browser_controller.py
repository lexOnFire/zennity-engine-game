from pathlib import Path
from types import SimpleNamespace

from editor.asset_browser_controller import AssetBrowserController


def test_asset_root_prefers_canonical_case_and_supports_legacy_case(tmp_path: Path) -> None:
    controller = AssetBrowserController(SimpleNamespace(), tmp_path, SimpleNamespace())
    legacy = tmp_path / "assets"
    legacy.mkdir()
    assert controller.asset_root() == legacy

    canonical = tmp_path / "Assets"
    canonical.mkdir()
    assert controller.asset_root() == canonical


def test_asset_classification_hides_internal_files_and_assigns_icons(tmp_path: Path) -> None:
    script = tmp_path / "player.py"
    animation = tmp_path / "walk.zanim"
    image = tmp_path / "hero.png"
    for path in (script, animation, image):
        path.touch()

    assert AssetBrowserController._hidden(script)
    assert AssetBrowserController.asset_icon(animation) == "🎞 "
    assert AssetBrowserController.asset_icon(image) == "🖼️ "
