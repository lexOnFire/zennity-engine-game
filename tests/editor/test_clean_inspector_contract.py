from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_inspector_exposes_standard_dynamic_cards() -> None:
    source = _source("editor/interface_smoke_test.py")
    expected = {
        "transform_header", "sprite_renderer_header", "audio_source_header",
        "rigidbody_header", "collider_header", "camera_header",
        "ui_component_header",
    }

    for attribute in expected:
        assert f"self.{attribute}" in source
    assert "inspector.setFixedWidth(280)" not in source
    assert "inspector_dock.setFixedWidth(290)" not in source


def test_inspector_only_shows_components_present_on_selected_object() -> None:
    source = _source("editor/isolated_editor_main.py")
    renderer_source = _source("editor/inspector_view_renderer.py")
    tree = ast.parse(source)
    update = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_update_inspector"
    )
    update_source = ast.get_source_segment(source, update) or ""

    for key in ("transform", "sprite", "audio", "rigidbody", "collider", "camera"):
        assert f'_set_inspector_card_present("{key}"' in renderer_source
    for key in ("ui", "logic", "runtime"):
        assert f'_set_inspector_card_present("{key}"' in renderer_source
    assert "self._inspector_view.render_physics(obj)" in update_source


def test_add_component_uses_searchable_picker_instead_of_flat_menu() -> None:
    editor_source = _source("editor/isolated_editor_main.py")
    picker_source = _source("editor/widgets/component_picker.py")
    editor_tree = ast.parse(editor_source)
    open_picker = next(
        node for node in ast.walk(editor_tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_open_add_component_menu"
    )
    method_source = ast.get_source_segment(editor_source, open_picker) or ""

    assert "ComponentPickerDialog" in method_source
    assert "QMenu(" not in method_source
    assert "Pesquisar componente..." in picker_source
    for category in ("Programação visual", "Renderização", "Física", "Câmera e áudio", "Interface"):
        assert category in picker_source


def test_component_card_expansion_state_is_preserved() -> None:
    source = _source("editor/isolated_editor_main.py")

    assert "self._component_expanded" in source
    assert '"audio": False' in source
    assert '"rigidbody": False' in source
    assert '"collider": False' in source
    assert 'self._component_expanded[f"script:{script_path}"] = True' in source
    assert "_toggle_dynamic_inspector_card" in source
