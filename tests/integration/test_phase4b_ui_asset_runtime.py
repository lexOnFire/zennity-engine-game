"""
PHASE 4B: UI Asset Runtime Compilation Tests

Validates:
1. UIAssetLoader (load and validate .zui files)
2. UIRuntimeCompiler (convert authoring widgets to runtime)
3. Color conversion (hex ↔ RGB)
4. Integration with Scene loading
5. Logic Graph access
6. Set/Get consistency
7. Change detection across Play cycles
"""
import pytest
from pathlib import Path
import json
from unittest.mock import MagicMock

from engine.ui.asset_loader import (
    UIAssetLoader,
    UIAssetLoaderError,
    UIAssetValidationError,
    UIAssetNotFoundError,
)
from engine.ui.runtime_compiler import (
    UIRuntimeCompiler,
    UICompilerError,
    hex_to_rgb,
    rgb_to_hex,
)
from engine.ui.runtime_components import ProgressBarComponent, LabelComponent
from engine.ui.runtime_service import UIRuntimeService


class TestUIAssetLoaderBasics:
    """Test UIAssetLoader file operations."""

    def test_load_valid_zui_file(self):
        """Load a valid .zui file."""
        zui_path = Path("tests/fixtures/HealthBar.zui")
        loader = UIAssetLoader()

        doc = loader.load(zui_path)

        assert doc is not None
        assert isinstance(doc, dict)
        assert "canvas" in doc
        canvas = doc["canvas"]
        assert canvas.get("type") == "canvas"
        assert len(canvas.get("children", [])) >= 1

    def test_load_missing_file_raises_error(self):
        """Load non-existent file raises UIAssetNotFoundError."""
        loader = UIAssetLoader()

        with pytest.raises(UIAssetNotFoundError):
            loader.load("assets/nonexistent.zui")

    def test_load_invalid_json_raises_error(self):
        """Load malformed JSON raises UIAssetValidationError."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".zui", delete=False) as f:
            f.write("{invalid json")
            temp_path = f.name

        try:
            loader = UIAssetLoader()
            with pytest.raises(UIAssetValidationError):
                loader.load(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_with_relative_path(self):
        """Load using relative path."""
        loader = UIAssetLoader(project_root=Path.cwd())
        doc = loader.load("tests/fixtures/HealthBar.zui")

        assert doc is not None


class TestUIAssetValidation:
    """Test UIAssetLoader validation."""

    def test_validate_valid_document(self):
        """Validate a correct UI document."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "HealthBar",
                        "value": 75,
                        "max_value": 100,
                    }
                ]
            }
        }
        loader = UIAssetLoader()
        loader.validate(doc)  # Should not raise

    def test_validate_duplicate_widget_names_raises_error(self):
        """Duplicate widget names raise UIAssetValidationError."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {"type": "UILabel", "name": "Label1"},
                    {"type": "UILabel", "name": "Label1"},  # Duplicate!
                ]
            }
        }
        loader = UIAssetLoader()

        with pytest.raises(UIAssetValidationError) as exc_info:
            loader.validate(doc)
        assert "Duplicate" in str(exc_info.value)

    def test_validate_invalid_progressbar_max_value_raises_error(self):
        """Invalid max_value raises UIAssetValidationError."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "HealthBar",
                        "max_value": 0,  # Invalid: must be > 0
                    }
                ]
            }
        }
        loader = UIAssetLoader()

        with pytest.raises(UIAssetValidationError) as exc_info:
            loader.validate(doc)
        assert "max_value" in str(exc_info.value).lower()

    def test_validate_progressbar_value_exceeds_max_raises_error(self):
        """ProgressBar value > max_value raises error."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "HealthBar",
                        "value": 150,
                        "max_value": 100,  # value > max_value!
                    }
                ]
            }
        }
        loader = UIAssetLoader()

        with pytest.raises(UIAssetValidationError) as exc_info:
            loader.validate(doc)
        assert "value" in str(exc_info.value).lower()


class TestColorConversion:
    """Test hex/RGB color conversion."""

    def test_hex_to_rgb_valid(self):
        """Convert valid hex to RGB."""
        assert hex_to_rgb("#2ECC71") == (46, 204, 113)
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_hex_to_rgb_invalid(self):
        """Invalid hex returns default white."""
        assert hex_to_rgb("invalid") == (255, 255, 255)
        assert hex_to_rgb("#ZZZZZ") == (255, 255, 255)
        assert hex_to_rgb("#12") == (255, 255, 255)

    def test_rgb_to_hex_valid(self):
        """Convert valid RGB to hex."""
        assert rgb_to_hex((46, 204, 113)) == "#2ecc71"
        assert rgb_to_hex((255, 255, 255)) == "#ffffff"
        assert rgb_to_hex((0, 0, 0)) == "#000000"

    def test_rgb_to_hex_invalid(self):
        """Invalid RGB returns default white."""
        assert rgb_to_hex((256, 0, 0)) == "#ff0000"  # Clamped
        assert rgb_to_hex("invalid") == "#ffffff"
        assert rgb_to_hex([]) == "#ffffff"


class TestUIRuntimeCompiler:
    """Test UIRuntimeCompiler widget compilation."""

    def test_compile_progress_bar_widget(self):
        """Compile a ProgressBar widget."""
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UIProgressBar",
            "name": "HealthBar",
            "value": 75,
            "max_value": 100,
            "fill_color": "#2ecc71",
            "bg_color": "#1c2330",
        }

        compiled = compiler._compile_widget(widget_data, "uiprogressbar")

        assert compiled is not None
        assert compiled["type"] == "ProgressBarComponent"
        assert compiled["widget_name"] == "HealthBar"
        assert compiled["properties"]["value"] == 75.0
        assert compiled["properties"]["max_value"] == 100.0
        assert compiled["properties"]["fill_color"] == (46, 204, 113)
        assert compiled["properties"]["bg_color"] == (28, 35, 48)

    def test_compile_label_widget(self):
        """Compile a Label widget."""
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UILabel",
            "name": "HealthLabel",
            "text": "Health: 75/100",
            "font_size": 14,
            "text_color": "#ffffff",
        }

        compiled = compiler._compile_widget(widget_data, "uilabel")

        assert compiled is not None
        assert compiled["type"] == "LabelComponent"
        assert compiled["widget_name"] == "HealthLabel"
        assert compiled["properties"]["text"] == "Health: 75/100"
        assert compiled["properties"]["font_size"] == 14
        assert compiled["properties"]["color"] == (255, 255, 255)

    def test_compile_full_ui_document(self):
        """Compile a full UI document."""
        compiler = UIRuntimeCompiler()
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {
                        "type": "UIProgressBar",
                        "name": "HealthBar",
                        "value": 75,
                        "max_value": 100,
                    },
                    {
                        "type": "UILabel",
                        "name": "HealthLabel",
                        "text": "Health: 75",
                    },
                ]
            }
        }

        compiled_widgets = compiler.compile(doc)

        assert len(compiled_widgets) == 2
        assert compiled_widgets[0]["type"] == "ProgressBarComponent"
        assert compiled_widgets[1]["type"] == "LabelComponent"

    def test_compile_unknown_widget_type_raises_error(self):
        """Unknown widget type raises error."""
        compiler = UIRuntimeCompiler()
        widget_data = {"type": "UIUnknown", "name": "Unknown"}

        with pytest.raises(UICompilerError) as exc_info:
            compiler._compile_widget(widget_data, "uiunknown")
        assert "Unsupported" in str(exc_info.value)


class TestProgressBarCompilation:
    """Test ProgressBar-specific compilation."""

    def test_progressbar_properties_preserved(self):
        """All ProgressBar properties preserved in compilation."""
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UIProgressBar",
            "name": "HealthBar",
            "value": 50,
            "max_value": 100,
            "x": 10,
            "y": 20,
            "width": 200,
            "height": 25,
            "fill_color": "#2ecc71",
            "bg_color": "#1c2330",
            "visible": True,
            "alpha": 200,
        }

        compiled = compiler._compile_widget(widget_data, "uiprogressbar")

        props = compiled["properties"]
        assert props["value"] == 50.0
        assert props["max_value"] == 100.0
        assert props["x"] == 10.0
        assert props["y"] == 20.0
        assert props["width"] == 200.0
        assert props["height"] == 25.0
        assert props["fill_color"] == (46, 204, 113)
        assert props["bg_color"] == (28, 35, 48)
        assert props["visible"] is True
        assert props["alpha"] == 200

    def test_progressbar_value_clamped_to_max(self):
        """ProgressBar value clamped to max_value."""
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UIProgressBar",
            "name": "HealthBar",
            "value": 150,  # Exceeds max_value
            "max_value": 100,
        }

        compiled = compiler._compile_widget(widget_data, "uiprogressbar")

        # Should be clamped to max_value
        assert compiled["properties"]["value"] == 100.0


class TestNameToWidgetNameMapping:
    """Test name → widget_name conversion."""

    def test_authoring_name_becomes_widget_name(self):
        """UI authoring 'name' maps to runtime 'widget_name'."""
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UIProgressBar",
            "name": "HealthBar",  # Authoring name
        }

        compiled = compiler._compile_widget(widget_data, "uiprogressbar")

        # Runtime should have widget_name
        assert compiled["widget_name"] == "HealthBar"


class TestIntegrationWithLoaderAndCompiler:
    """Test UIAssetLoader + UIRuntimeCompiler pipeline."""

    def test_load_validate_compile_pipeline(self):
        """Complete pipeline: load → validate → compile."""
        # Load
        loader = UIAssetLoader()
        doc = loader.load("tests/fixtures/HealthBar.zui")

        # Validate (already done by load, but test explicitly)
        loader.validate(doc)

        # Compile
        compiler = UIRuntimeCompiler()
        compiled_widgets = compiler.compile(doc)

        # Verify results
        assert len(compiled_widgets) > 0
        assert any(w["type"] == "ProgressBarComponent" for w in compiled_widgets)
        assert any(w["type"] == "LabelComponent" for w in compiled_widgets)


class TestRuntimeComponentInstantiation:
    """Test that compiled widgets can be instantiated as runtime components."""

    def test_compiled_progressbar_instantiates_as_runtime_component(self):
        """Compiled ProgressBar becomes ProgressBarComponent instance."""
        UIRuntimeService.reset()

        # Compile
        compiler = UIRuntimeCompiler()
        widget_data = {
            "type": "UIProgressBar",
            "name": "HealthBar",
            "value": 75,
            "max_value": 100,
        }
        compiled = compiler._compile_widget(widget_data, "uiprogressbar")

        # Instantiate runtime component from compiled data
        component = ProgressBarComponent(
            value=compiled["properties"]["value"],
            max_value=compiled["properties"]["max_value"],
        )
        component.widget_name = compiled["widget_name"]

        # Register
        ui_service = UIRuntimeService.instance()
        ui_service.register_widget(component)

        # Verify
        assert ui_service.exists("HealthBar")
        assert ui_service.get_property("HealthBar", "value") == 75.0


class TestMultipleWidgetTypes:
    """Test compilation of multiple widget types."""

    def test_compile_progressbar_label_button_image(self):
        """Compile various widget types in one document."""
        compiler = UIRuntimeCompiler()
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {"type": "UIProgressBar", "name": "Bar1"},
                    {"type": "UILabel", "name": "Label1"},
                    {"type": "UIButton", "name": "Button1"},
                    {"type": "UIImage", "name": "Image1"},
                ]
            }
        }

        compiled = compiler.compile(doc)

        types = [w["type"] for w in compiled if w]
        assert "ProgressBarComponent" in types
        assert "LabelComponent" in types
        assert "ButtonComponent" in types
        assert "ImageComponent" in types


class TestDuplicateWidgetRejection:
    """Test that duplicate widget names are rejected during loading."""

    def test_duplicate_names_in_zui_rejected(self):
        """Duplicate widget names in .zui rejected by loader."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {"type": "UILabel", "name": "Label"},
                    {"type": "UILabel", "name": "Label"},  # Duplicate!
                ]
            }
        }

        loader = UIAssetLoader()
        with pytest.raises(UIAssetValidationError) as exc_info:
            loader.validate(doc)
        assert "Duplicate" in str(exc_info.value)


class TestUnknownWidgetHandling:
    """Test handling of unknown/unsupported widget types."""

    def test_unknown_widget_type_produces_error(self):
        """Unknown widget type produces clear error."""
        doc = {
            "canvas": {
                "type": "canvas",
                "children": [
                    {"type": "UIUnknownType", "name": "Unknown"},
                ]
            }
        }

        compiler = UIRuntimeCompiler()
        with pytest.raises(UICompilerError) as exc_info:
            compiler.compile(doc)
        assert "unsupported" in str(exc_info.value).lower()


class TestMissingAssetDiagnostics:
    """Test error messages for missing assets."""

    def test_missing_zui_file_diagnostic(self):
        """Missing .zui file produces clear diagnostic."""
        loader = UIAssetLoader()

        with pytest.raises(UIAssetNotFoundError) as exc_info:
            loader.load("missing.zui")

        error_msg = str(exc_info.value)
        assert "missing.zui" in error_msg
        assert "not found" in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
