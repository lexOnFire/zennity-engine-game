"""
PHASE 4B: E2E Tests - UI Asset → Logic Graph Access

Complete pipeline test:
1. Load .zui asset
2. Compile to runtime components
3. Auto-register in UIRuntimeService
4. Logic Graph accesses via get_progress_bar_value
5. Set/Get consistency
"""
import pytest
from unittest.mock import MagicMock
from pathlib import Path

from engine.ui.asset_loader import UIAssetLoader
from engine.ui.runtime_compiler import UIRuntimeCompiler
from engine.ui.runtime_components import ProgressBarComponent, LabelComponent
from engine.ui.runtime_service import (
    UIRuntimeService,
    UIWidgetNotFoundError,
)
from engine.logic.runtime.nodes.dynamic_ui_nodes import evaluate_get_progress_bar_value


class TestE2EUIAssetToLogicGraph:
    """Test complete pipeline from .zui asset to Logic Graph access."""

    def setup_method(self):
        """Reset service before each test."""
        UIRuntimeService.reset()

    def test_complete_pipeline_zui_to_logic_graph_read(self):
        """
        E2E: Load .zui → Compile → Register → Logic Graph reads value
        """
        # 1. Load .zui asset
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        # 2. Compile to runtime components
        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)

        # 3. Instantiate and register runtime components
        ui_service = UIRuntimeService.instance()

        # Find ProgressBar and instantiate
        prog_bar_data = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"),
            None,
        )
        assert prog_bar_data is not None

        # Create component from compiled data
        pb_component = ProgressBarComponent(
            value=prog_bar_data["properties"]["value"],
            max_value=prog_bar_data["properties"]["max_value"],
        )
        pb_component.widget_name = prog_bar_data["widget_name"]
        pb_component.game_object = MagicMock()

        # Auto-register via lifecycle
        pb_component.on_runtime_start()

        # 4. Verify Logic Graph can read
        # Simulate Logic Graph evaluating get_progress_bar_value
        runtime = MagicMock()
        runtime._read_input.return_value = "HealthBar"
        runtime._store.side_effect = lambda node_id, key, val: val

        node = {"id": "test_node", "properties": {"widget_name": "HealthBar"}}
        game = MagicMock()

        result = evaluate_get_progress_bar_value(
            runtime, "test_node", "value", node, game, 0.016, set()
        )

        # Verify: Value from .zui (75) is accessible to Logic Graph
        assert result == 75.0

    def test_compiled_progressbar_set_get_consistency(self):
        """Compiled ProgressBar: Set/Get use same instance."""
        # Load and compile
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)

        ui_service = UIRuntimeService.instance()

        # Create and register
        prog_bar_data = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"), None
        )
        pb_component = ProgressBarComponent(
            value=prog_bar_data["properties"]["value"],
            max_value=prog_bar_data["properties"]["max_value"],
        )
        pb_component.widget_name = prog_bar_data["widget_name"]
        pb_component.game_object = MagicMock()
        pb_component.on_runtime_start()

        # Set new value
        ui_service.set_property("HealthBar", "value", 50.0)

        # Get should return set value
        new_value = ui_service.get_property("HealthBar", "value")
        assert new_value == 50.0

        # Verify instance was modified
        assert pb_component.value == 50.0

    def test_compiled_multiple_widgets_no_crosstalk(self):
        """Multiple compiled widgets don't interfere."""
        # Load and compile
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)

        ui_service = UIRuntimeService.instance()

        # Find both ProgressBar and Label
        prog_bar_data = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"), None
        )
        label_data = next(
            (w for w in compiled_widgets if w["type"] == "LabelComponent"), None
        )

        # Register ProgressBar
        pb = ProgressBarComponent(
            value=prog_bar_data["properties"]["value"],
            max_value=prog_bar_data["properties"]["max_value"],
        )
        pb.widget_name = prog_bar_data["widget_name"]
        pb.game_object = MagicMock()
        pb.on_runtime_start()

        # Register Label
        label = LabelComponent(text=label_data["properties"]["text"])
        label.widget_name = label_data["widget_name"]
        label.game_object = MagicMock()
        label.on_runtime_start()

        # Verify each returns correct value
        health_value = ui_service.get_property("HealthBar", "value")
        health_label = ui_service.get_property("HealthLabel", "text")

        assert health_value == 75.0
        assert health_label == "Health: 75/100"

        # Modify one, verify other is unchanged
        ui_service.set_property("HealthBar", "value", 30.0)
        assert ui_service.get_property("HealthLabel", "text") == "Health: 75/100"

    def test_compiled_widget_no_legacy_fallback_needed(self):
        """
        Compiled widgets accessed directly via UIRuntimeService,
        NOT via legacy fallback paths.
        """
        # Load, compile, register
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)

        ui_service = UIRuntimeService.instance()

        prog_bar_data = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"), None
        )
        pb = ProgressBarComponent(
            value=prog_bar_data["properties"]["value"],
            max_value=prog_bar_data["properties"]["max_value"],
        )
        pb.widget_name = prog_bar_data["widget_name"]
        pb.game_object = MagicMock()
        pb.on_runtime_start()

        # The widget is now in UIRuntimeService
        # Verify it exists (not via fallback)
        assert ui_service.exists("HealthBar")

        # Get value without needing fallback path
        value = ui_service.get_property("HealthBar", "value")
        assert value == 75.0

    def test_compiled_progressbar_lifecycle_destroy(self):
        """Compiled ProgressBar cleanup on destroy."""
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)

        ui_service = UIRuntimeService.instance()

        prog_bar_data = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"), None
        )
        pb = ProgressBarComponent(
            value=prog_bar_data["properties"]["value"],
            max_value=prog_bar_data["properties"]["max_value"],
        )
        pb.widget_name = prog_bar_data["widget_name"]
        pb.game_object = MagicMock()
        pb.on_runtime_start()

        # Verify registered
        assert ui_service.exists("HealthBar")

        # Destroy
        pb.destroy()

        # Verify unregistered
        assert not ui_service.exists("HealthBar")

    def test_compiled_progressbar_properties_match_source(self):
        """All .zui properties transferred to compiled component."""
        loader = UIAssetLoader()
        ui_doc = loader.load("tests/fixtures/HealthBar.zui")

        # Extract source ProgressBar properties
        canvas = ui_doc.get("canvas", ui_doc)
        source_pb = next(
            (c for c in canvas.get("children", []) if c.get("type") == "UIProgressBar"),
            None,
        )

        # Compile
        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(ui_doc)
        compiled_pb = next(
            (w for w in compiled_widgets if w["type"] == "ProgressBarComponent"), None
        )

        # Verify key properties transferred
        props = compiled_pb["properties"]
        assert props["value"] == float(source_pb["value"])
        assert props["max_value"] == float(source_pb["max_value"])
        assert props["x"] == float(source_pb["x"])
        assert props["y"] == float(source_pb["y"])
        assert props["width"] == float(source_pb["width"])
        assert props["height"] == float(source_pb["height"])
        assert props["visible"] is bool(source_pb.get("visible", True))

    def test_widget_name_from_authoring_name(self):
        """
        Authoring widget 'name' becomes runtime 'widget_name'.
        Logic Graph uses this to resolve the widget.
        """
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "PlayerHealth",  # Authoring name
                        "value": 100,
                        "max_value": 100,
                    }
                ]
            }
        }

        compiler = UIRuntimeCompiler()
        compiled = compiler.compile(doc)

        pb_data = compiled[0]
        assert pb_data["widget_name"] == "PlayerHealth"

        # When instantiated and registered...
        ui_service = UIRuntimeService.instance()
        pb = ProgressBarComponent(value=100, max_value=100)
        pb.widget_name = pb_data["widget_name"]
        pb.game_object = MagicMock()
        pb.on_runtime_start()

        # ...Logic Graph can find by that name
        assert ui_service.exists("PlayerHealth")

    def test_zui_to_progressbar_component_all_types_work(self):
        """Test that various property types convert correctly."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "TestBar",
                        "value": 42,  # int
                        "max_value": 100.5,  # float
                        "x": 10,
                        "y": 20.5,
                        "width": 150,
                        "height": 25.0,
                        "visible": True,  # bool
                        "alpha": 200,
                        "fill_color": "#2ecc71",  # hex string
                        "bg_color": [28, 35, 48],  # RGB list
                    }
                ]
            }
        }

        compiler = UIRuntimeCompiler()
        compiled = compiler.compile(doc)

        pb_data = compiled[0]
        props = pb_data["properties"]

        # Verify all types converted and stored correctly
        assert isinstance(props["value"], float)
        assert isinstance(props["max_value"], float)
        assert isinstance(props["x"], float)
        assert isinstance(props["y"], float)
        assert isinstance(props["width"], float)
        assert isinstance(props["height"], float)
        assert isinstance(props["visible"], bool)
        assert isinstance(props["alpha"], int)
        assert isinstance(props["fill_color"], tuple)
        assert len(props["fill_color"]) == 3
        assert isinstance(props["bg_color"], tuple)
        assert len(props["bg_color"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
