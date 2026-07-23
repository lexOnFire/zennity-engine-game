from pathlib import Path


def test_component_addition_is_owned_by_inspector_controller() -> None:
    editor = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    controller = Path("editor/inspector_controller.py").read_text(encoding="utf-8")

    assert "self._inspector_components.add_component(component)" in editor
    assert "def add_component(self, component: str)" in controller
    assert 'if component == "animator"' in controller
    assert 'if component == "logic"' in controller
    assert 'elif component == "camera"' in controller
    assert 'elif component.startswith("ui_")' in controller


def test_standard_component_defaults_have_one_addition_owner() -> None:
    editor = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    controller = Path("editor/inspector_controller.py").read_text(encoding="utf-8")

    assert '"gravity_scale": 1.0' not in editor[editor.index("def _add_component"):]
    assert '"gravity_scale": 1.0' in controller
    assert '"background_color": [22, 24, 31]' in controller
