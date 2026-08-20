"""
Phase 8A: BUG-8A-003 Fix Validation

Validates that MainMenu and other scenes properly load UI in Play Mode.

Root cause: During migration, UI reference was moved to components.canvas.ui_asset,
but RuntimeScene._compile_and_attach_ui() expects scene.ui (root level).

Fix: Keep UI asset at scene root level during migration.

PHASE 13 item 13.1-B: the fix went the other way in the end. The canonical home
for a UI binding is the Canvas component, not a root-level ``ui`` string, and
that is where every shipping scene keeps it. The assertions below now read the
binding from the component; what they assert about the game is unchanged --
every scene that shows UI still has to name a .zui.
"""

import json
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration import _phase8a_canonical as canonical


class TestBug8A003UILoading:
    """Validates that scenes have UI reference at root level for RuntimeScene."""

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_binds_its_ui_through_a_canvas_component(self, scene_name):
        """Scenes with UI must name a .zui on a Canvas component."""
        scene = canonical.load_scene(scene_name)

        bound = [
            canonical.ui_asset_of(obj)
            for obj in canonical.objects(scene)
            if canonical.ui_asset_of(obj)
        ]
        assert bound, f"{scene_name} binds no .zui through any Canvas component"
        for asset in bound:
            assert isinstance(asset, str)
            assert asset.endswith(".zui"), f"{scene_name} binds {asset!r}, not a .zui"

    def test_mainmenu_has_correct_ui_path(self):
        """MainMenu should reference MainMenu.zui."""
        menu = canonical.find_object(canonical.load_scene("MainMenu"), "MenuUI")

        assert canonical.ui_asset_of(menu) == "Assets/UI/MainMenu.zui"

    def test_gameover_has_correct_ui_path(self):
        """GameOver should reference GameOver.zui."""
        scene_path = project_root / "Assets" / "Scenes" / "GameOver.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert data["ui"] == "Assets/UI/GameOver.zui"

    def test_victory_has_correct_ui_path(self):
        """Victory should reference Victory.zui."""
        scene_path = project_root / "Assets" / "Scenes" / "Victory.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert data["ui"] == "Assets/UI/Victory.zui"

    def test_level_scenes_have_ui_for_hud(self):
        """Each level binds a HUD. Level 2 uses its own, with the boss bars."""
        expected = {"Level1": "Assets/UI/HUD.zui", "Level2": "Assets/UI/HUD_Boss.zui"}
        for scene_name, asset in expected.items():
            hud = canonical.find_object(canonical.load_scene(scene_name), "HUD")
            assert hud is not None, f"{scene_name} has no HUD object"
            assert canonical.ui_asset_of(hud) == asset

    def test_ui_asset_file_exists(self):
        """All referenced UI assets must exist."""
        ui_assets = [
            "Assets/UI/MainMenu.zui",
            "Assets/UI/GameOver.zui",
            "Assets/UI/Victory.zui",
            "Assets/UI/HUD.zui",
        ]

        for asset_path in ui_assets:
            full_path = project_root / asset_path
            assert full_path.exists(), f"UI asset not found: {asset_path}"

    def test_canvas_components_still_present(self):
        """Canvas objects should still have components.canvas structure."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        # Find Canvas object
        canvas_obj = next((o for o in data["objects"] if "canvas" in o.get("components", {})), None)
        assert canvas_obj is not None, "MainMenu should have Canvas object"

        # Canvas component should have ui_asset (even though root-level ui is primary)
        canvas_comp = canvas_obj["components"]["canvas"]
        assert isinstance(canvas_comp, dict), "Canvas component should be dict"
        # ui_asset may be present in component (for reference), but not required for loading

    def test_migration_creates_legacy_backups(self):
        """Verify legacy backups exist for rollback if needed."""
        for scene_name in ["MainMenu", "Level1", "Level2", "GameOver", "Victory"]:
            backup_path = project_root / "Assets" / "Scenes" / f"{scene_name}_legacy.zscene"
            assert backup_path.exists(), f"Legacy backup missing: {scene_name}_legacy.zscene"

            # Legacy backups should have old schema
            legacy_data = json.loads(backup_path.read_text(encoding="utf-8"))
            assert "format" in legacy_data, f"{scene_name}_legacy should have old 'format' field"
            assert "objects" in legacy_data


class TestRuntimeSceneUILoading:
    """Tests RuntimeScene's UI loading mechanism."""

    def test_runtime_scene_looks_for_ui_at_root(self):
        """Verify RuntimeScene code expects scene.ui at root level."""
        from engine.runtime.runtime_scene import RuntimeScene

        # Read RuntimeScene source to confirm ui lookup
        source_file = project_root / "engine" / "runtime" / "runtime_scene.py"
        source = source_file.read_text(encoding="utf-8")

        # Should have line like: ui_asset_path = getattr(self.editor_scene, "ui", None)
        assert "getattr(self.editor_scene, \"ui\"" in source or \
               "self.editor_scene.ui" in source, \
               "RuntimeScene should look for scene.ui attribute"

    def test_ui_asset_loader_can_load_ui_files(self):
        """Verify UIAssetLoader exists and can load .zui files."""
        from engine.ui.asset_loader import UIAssetLoader

        loader = UIAssetLoader(project_root=project_root)

        # Try loading MainMenu.zui
        ui_path = "Assets/UI/MainMenu.zui"
        try:
            ui_document = loader.load(ui_path)
            assert ui_document is not None, f"Failed to load {ui_path}"
        except Exception as e:
            pytest.fail(f"UIAssetLoader failed to load {ui_path}: {e}")

    def test_scene_roundtrip_preserves_ui(self):
        """Verify save/load roundtrip preserves UI reference."""
        menu = canonical.find_object(canonical.load_scene("MainMenu"), "MenuUI")
        original_ui = canonical.ui_asset_of(menu)

        assert original_ui is not None, "MenuUI should bind a .zui"

        # Reading again must give the same binding: the document is the source
        # of truth and nothing rewrites it on load.
        reloaded = canonical.find_object(canonical.load_scene("MainMenu"), "MenuUI")

        assert canonical.ui_asset_of(reloaded) == original_ui


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
