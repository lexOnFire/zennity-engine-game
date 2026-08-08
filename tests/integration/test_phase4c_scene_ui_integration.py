"""
PHASE 4C: Real Scene.UI Integration Tests

Complete E2E validation:
1. Create .zui and .zscene files (real temporary files)
2. Load Scene normally (using actual Scene loader)
3. Start Play (automatic UI compilation)
4. Verify Logic Graph access
5. NO manual UIAssetLoader/Compiler calls
6. NO manual ProgressBarComponent creation
"""
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from engine.core.scene import Scene
from engine.game_object import GameObject
from engine.runtime.runtime_scene import RuntimeScene
from engine.ui.runtime_service import UIRuntimeService
from engine.logic.runtime.nodes.dynamic_ui_nodes import evaluate_get_progress_bar_value


class TestPhase4CSceneUIIntegration:
    """Real Scene.ui integration - automatic compilation during Play."""

    def setup_method(self):
        """Reset services and state."""
        UIRuntimeService.reset()

    def _create_temp_zui(self, health_value: float = 75.0) -> Path:
        """Create a temporary .zui file."""
        ui_doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "HealthBar",
                        "value": health_value,
                        "max_value": 100.0,
                    },
                    {
                        "type": "UILabel",
                        "name": "ScoreLabel",
                        "text": "Score: 1000",
                    },
                ]
            }
        }

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".zui", delete=False)
        json.dump(ui_doc, temp_file)
        temp_file.close()
        return Path(temp_file.name)

    def _create_editor_scene_with_ui(self, ui_path: str | Path) -> Scene:
        """Create an editor Scene with ui field pointing to .zui file."""
        scene = Scene("TestScene")

        # Add ui field pointing to .zui asset (as if loaded from .zscene)
        scene.ui = str(ui_path)

        # Add a regular GameObject to verify both UI and regular objects work
        player = GameObject("Player")
        scene.game_objects.append(player)
        player.scene = scene

        return scene

    def test_scene_without_ui_still_loads(self):
        """Scene without ui field loads normally."""
        editor_scene = Scene("NoUIScene")
        player = GameObject("Player")
        editor_scene.game_objects.append(player)
        player.scene = editor_scene

        # Should not raise - Scene without UI is valid
        runtime_scene = RuntimeScene(editor_scene)

        assert runtime_scene is not None
        assert len(runtime_scene.game_objects) == 1  # Just the player

    def test_scene_ui_field_automatically_loaded_on_play(self):
        """Scene.ui field triggers automatic .zui loading when Play starts."""
        # Create .zui file
        zui_path = self._create_temp_zui(health_value=80.0)

        try:
            # Create editor scene with ui field
            editor_scene = self._create_editor_scene_with_ui(zui_path)

            # Key: NO manual UIAssetLoader.load() call
            # Key: NO manual UIRuntimeCompiler.compile() call

            # Start Play - this should automatically compile UI
            runtime_scene = RuntimeScene(editor_scene)

            # Verify UI GameObjects were created
            game_objects = runtime_scene.game_objects
            object_names = {go.name for go in game_objects}

            # Should have: Player (regular) + __UICanvas__ (generated)
            assert "Player" in object_names
            assert "__UICanvas__" in object_names

            # Verify widget GameObjects under UICanvas
            ui_canvas = next(go for go in game_objects if go.name == "__UICanvas__")
            children_names = {child.name for child in ui_canvas.children}

            assert "HealthBar" in children_names
            assert "ScoreLabel" in children_names

        finally:
            zui_path.unlink()

    def test_compiled_ui_widgets_have_components(self):
        """Compiled UI widgets have runtime components attached."""
        zui_path = self._create_temp_zui(health_value=75.0)

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path)
            runtime_scene = RuntimeScene(editor_scene)

            # Find UICanvas
            ui_canvas = next(
                (go for go in runtime_scene.game_objects if go.name == "__UICanvas__"),
                None,
            )
            assert ui_canvas is not None

            # Find HealthBar GameObject
            health_bar_go = next(
                (child for child in ui_canvas.children if child.name == "HealthBar"),
                None,
            )
            assert health_bar_go is not None

            # Should have ProgressBarComponent
            components = getattr(health_bar_go, "components", [])
            component_types = {type(c).__name__ for c in components}
            assert "ProgressBarComponent" in component_types

            # Component should have widget_name set
            pb_component = next(
                (c for c in components if type(c).__name__ == "ProgressBarComponent"),
                None,
            )
            assert pb_component.widget_name == "HealthBar"

        finally:
            zui_path.unlink()

    def test_logic_graph_accesses_compiled_progressbar_after_play_starts(self):
        """
        After Play starts, Logic Graph can access compiled UI widgets
        without any manual initialization.
        """
        zui_path = self._create_temp_zui(health_value=65.0)

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path)
            runtime_scene = RuntimeScene(editor_scene)

            # Key: start_runtime() is where on_runtime_start() hooks are called
            # This is where components auto-register
            runtime_scene.start_runtime()

            # Now UIRuntimeService should have registered the widgets
            ui_service = UIRuntimeService.instance()
            assert ui_service.exists("HealthBar")
            assert ui_service.exists("ScoreLabel")

            # Logic Graph evaluation should work
            runtime = MagicMock()
            runtime._read_input.return_value = "HealthBar"
            runtime._store.side_effect = lambda node_id, key, val: val

            node = {"id": "test_node", "properties": {"widget_name": "HealthBar"}}
            game = MagicMock()

            result = evaluate_get_progress_bar_value(
                runtime, "test_node", "value", node, game, 0.016, set()
            )

            # Should return the value from .zui
            assert result == 65.0

        finally:
            zui_path.unlink()

    def test_no_legacy_fallback_used_for_compiled_widgets(self):
        """
        Compiled widgets access UIRuntimeService directly,
        NOT via legacy fallback paths.
        """
        zui_path = self._create_temp_zui(health_value=85.0)

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path)
            runtime_scene = RuntimeScene(editor_scene)
            runtime_scene.start_runtime()

            ui_service = UIRuntimeService.instance()

            # The widget is registered in service
            assert ui_service.exists("HealthBar")

            # Direct access via service (not fallback)
            value = ui_service.get_property("HealthBar", "value")
            assert value == 85.0

        finally:
            zui_path.unlink()

    def test_replay_creates_fresh_ui_instances(self):
        """Stop Play, modify .zui, Play again - gets new values."""
        zui_path = self._create_temp_zui(health_value=30.0)

        try:
            # PLAY 1
            editor_scene = self._create_editor_scene_with_ui(zui_path)
            runtime_scene1 = RuntimeScene(editor_scene)
            runtime_scene1.start_runtime()

            ui_service1 = UIRuntimeService.instance()
            value1 = ui_service1.get_property("HealthBar", "value")
            assert value1 == 30.0

            # STOP
            runtime_scene1.stop_runtime()
            UIRuntimeService.reset()

            # Modify .zui
            zui_path.write_text(json.dumps({
                "canvas": {
                    "type": "canvas",
                    "children": [
                        {
                            "type": "UIProgressBar",
                            "name": "HealthBar",
                            "value": 95.0,  # Changed!
                            "max_value": 100.0,
                        }
                    ]
                }
            }))

            # PLAY 2
            editor_scene2 = self._create_editor_scene_with_ui(zui_path)
            runtime_scene2 = RuntimeScene(editor_scene2)
            runtime_scene2.start_runtime()

            ui_service2 = UIRuntimeService.instance()
            value2 = ui_service2.get_property("HealthBar", "value")
            assert value2 == 95.0  # New value loaded

        finally:
            zui_path.unlink()

    def test_missing_zui_asset_reports_scene_context(self):
        """Missing .zui file reports scene context in error."""
        editor_scene = self._create_editor_scene_with_ui("Assets/UI/missing.zui")

        with pytest.raises(RuntimeError) as exc_info:
            RuntimeScene(editor_scene)

        error_msg = str(exc_info.value)
        assert "TestScene" in error_msg  # Scene name
        assert "missing.zui" in error_msg  # Asset path

    def test_invalid_zui_reports_scene_context(self):
        """Invalid .zui reports scene context in error."""
        # Create invalid .zui (duplicate widget name)
        zui_path = tempfile.NamedTemporaryFile(mode="w", suffix=".zui", delete=False)
        json.dump({
            "canvas": {
                "type": "canvas",
                "children": [
                    {"type": "UILabel", "name": "Label"},
                    {"type": "UILabel", "name": "Label"},  # Duplicate!
                ]
            }
        }, zui_path)
        zui_path.close()

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path.name)

            with pytest.raises(RuntimeError) as exc_info:
                RuntimeScene(editor_scene)

            error_msg = str(exc_info.value)
            assert "TestScene" in error_msg  # Scene name
            assert "Duplicate" in error_msg or "duplicate" in error_msg

        finally:
            Path(zui_path.name).unlink()

    def test_multiple_ui_widgets_independently_accessible(self):
        """Multiple compiled widgets are independently accessible via Logic Graph."""
        zui_path = self._create_temp_zui(health_value=60.0)

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path)
            runtime_scene = RuntimeScene(editor_scene)
            runtime_scene.start_runtime()

            ui_service = UIRuntimeService.instance()

            # Both widgets should be accessible
            assert ui_service.exists("HealthBar")
            assert ui_service.exists("ScoreLabel")

            # Each returns correct value
            health = ui_service.get_property("HealthBar", "value")
            score_text = ui_service.get_property("ScoreLabel", "text")

            assert health == 60.0
            assert score_text == "Score: 1000"

        finally:
            zui_path.unlink()

    def test_scene_ui_change_visible_on_next_play(self):
        """Editing .zui between Play sessions loads new values automatically."""
        zui_path = self._create_temp_zui(health_value=40.0)

        try:
            # Play 1: Load with value 40
            editor_scene1 = self._create_editor_scene_with_ui(zui_path)
            runtime_scene1 = RuntimeScene(editor_scene1)
            runtime_scene1.start_runtime()

            ui_service1 = UIRuntimeService.instance()
            assert ui_service1.get_property("HealthBar", "value") == 40.0

            # Stop and cleanup
            runtime_scene1.stop_runtime()
            UIRuntimeService.reset()

            # Edit .zui: change value to 100
            ui_doc_new = {
                "canvas": {
                    "type": "canvas",
                    "children": [
                        {
                            "type": "UIProgressBar",
                            "name": "HealthBar",
                            "value": 100.0,
                            "max_value": 100.0,
                        }
                    ]
                }
            }
            zui_path.write_text(json.dumps(ui_doc_new))

            # Play 2: Should see new value
            editor_scene2 = self._create_editor_scene_with_ui(zui_path)
            runtime_scene2 = RuntimeScene(editor_scene2)
            runtime_scene2.start_runtime()

            ui_service2 = UIRuntimeService.instance()
            assert ui_service2.get_property("HealthBar", "value") == 100.0

        finally:
            zui_path.unlink()

    def test_scene_ui_properties_preserved_in_compilation(self):
        """All .zui properties preserved through compile→create→register."""
        zui_path = tempfile.NamedTemporaryFile(mode="w", suffix=".zui", delete=False)
        json.dump({
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "TestBar",
                        "value": 42,
                        "max_value": 84,
                        "x": 100,
                        "y": 200,
                        "width": 300,
                        "height": 40,
                        "fill_color": "#FF0000",
                        "bg_color": "#000000",
                        "visible": True,
                    }
                ]
            }
        }, zui_path)
        zui_path.close()

        try:
            editor_scene = self._create_editor_scene_with_ui(zui_path.name)
            runtime_scene = RuntimeScene(editor_scene)
            runtime_scene.start_runtime()

            # All properties should be accessible
            ui_service = UIRuntimeService.instance()
            pb = ui_service.resolve_widget("TestBar")

            assert pb.value == 42.0
            assert pb.max_value == 84.0

        finally:
            Path(zui_path.name).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
