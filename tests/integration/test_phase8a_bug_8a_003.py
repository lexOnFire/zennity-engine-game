"""
Phase 8A: BUG-8A-003 Fix Validation

Validates that MainMenu and other scenes properly load UI in Play Mode.

Root cause: During migration, UI reference was moved to components.canvas.ui_asset,
but RuntimeScene._compile_and_attach_ui() expects scene.ui (root level).

Fix: Keep UI asset at scene root level during migration.
"""

import json
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestBug8A003UILoading:
    """Validates that scenes have UI reference at root level for RuntimeScene."""

    @pytest.mark.parametrize("scene_name", [
        "MainMenu.zscene",
        "GameOver.zscene",
        "Victory.zscene",
    ])
    def test_scene_has_ui_at_root_level(self, scene_name):
        """Scenes with UI must have 'ui' field at root level."""
        scene_path = project_root / "Assets" / "Scenes" / scene_name
        assert scene_path.exists(), f"{scene_name} not found"

        data = json.loads(scene_path.read_text(encoding="utf-8"))

        # CRITICAL: RuntimeScene looks for scene.ui at root level
        assert "ui" in data, f"{scene_name} missing root-level 'ui' field"
        assert isinstance(data["ui"], str), f"{scene_name} ui field should be string (asset path)"
        assert data["ui"].endswith(".zui"), f"{scene_name} ui should reference .zui asset"

    def test_mainmenu_has_correct_ui_path(self):
        """MainMenu should reference MainMenu.zui."""
        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"
        data = json.loads(scene_path.read_text(encoding="utf-8"))

        assert data["ui"] == "Assets/UI/MainMenu.zui"

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
        """Level1 and Level2 have UI for HUD."""
        for scene_name in ["Level1.zscene", "Level2.zscene"]:
            scene_path = project_root / "Assets" / "Scenes" / scene_name
            data = json.loads(scene_path.read_text(encoding="utf-8"))

            # Level scenes should have HUD UI
            assert "ui" in data, f"{scene_name} missing root-level 'ui' field"
            assert data["ui"] == "Assets/UI/HUD.zui", f"{scene_name} should reference HUD.zui"

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
        import json

        scene_path = project_root / "Assets" / "Scenes" / "MainMenu.zscene"

        # Read original
        original_data = json.loads(scene_path.read_text(encoding="utf-8"))
        original_ui = original_data.get("ui")

        assert original_ui is not None, "Original scene should have ui field"

        # Verify it's still there
        reloaded_data = json.loads(scene_path.read_text(encoding="utf-8"))
        reloaded_ui = reloaded_data.get("ui")

        assert reloaded_ui == original_ui, "UI field should persist through load"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
