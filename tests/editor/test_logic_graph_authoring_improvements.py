import json

from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph_editor import LogicGraphEditor
from engine.logic.code_preview import node_code_preview
from engine.logic.graph_asset import create_logic_node


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_logic_clipboard_preserves_internal_connections(tmp_path):
    app = _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    first = create_logic_node("event_start", (10.0, 20.0))
    second = create_logic_node("move_by", (280.0, 20.0))
    editor.graph["nodes"] = [first, second]
    editor.graph["edges"] = [{
        "id": "edge",
        "from_node": first["id"],
        "from_port": "next",
        "to_node": second["id"],
        "to_port": "in",
        "kind": "flow",
    }]
    editor.set_graph(editor.graph)
    for item in editor.node_items.values():
        item.setSelected(True)

    assert editor.copy_selected()
    payload = json.loads(app.clipboard().text())
    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1
    assert editor.paste_selected()
    assert len(editor.graph["nodes"]) == 4
    assert len(editor.graph["edges"]) == 2


def test_recovery_path_remains_a_loadable_zlogic_path(tmp_path):
    _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    source = tmp_path / "Assets" / "Logic" / "Player.zlogic"
    recovery = editor._recovery_path(source)
    assert recovery.name == "Player.zlogic.autosave.zlogic"
    assert recovery.suffix == ".zlogic"


def test_code_preview_is_english_and_uses_editable_rotation_value():
    node = create_logic_node("rotate", (0.0, 0.0))
    node["properties"]["degrees"] = 180

    preview = node_code_preview(node)

    assert "target.rotation += 180" in preview
    assert "alvo" not in preview
    assert "rotação" not in preview


def test_code_preview_value_edit_updates_rotate_node(monkeypatch, tmp_path):
    _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    node = create_logic_node("rotate", (0.0, 0.0))
    editor.graph["nodes"] = [node]
    editor.set_graph(editor.graph)
    node_item = next(iter(editor.node_items.values()))

    monkeypatch.setattr(editor, "_request_code_value_edits", lambda *args, **kwargs: {"degrees": 180.0})

    assert editor.edit_node_code_value(node_item)
    assert node_item.node["properties"]["degrees"] == 180
    assert "target.rotation += 180" in node_item.code_item.toPlainText()


def test_code_preview_value_edit_updates_multiple_node_values(monkeypatch, tmp_path):
    _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    node = create_logic_node("move_by", (0.0, 0.0))
    editor.graph["nodes"] = [node]
    editor.set_graph(editor.graph)
    node_item = next(iter(editor.node_items.values()))

    monkeypatch.setattr(editor, "_request_code_value_edits", lambda *args, **kwargs: {"x": 180.0, "y": -45.0})

    assert editor.edit_node_code_value(node_item)
    assert node_item.node["properties"]["x"] == 180
    assert node_item.node["properties"]["y"] == -45
    assert "target.x += 180 * dt" in node_item.code_item.toPlainText()
    assert "target.y += -45 * dt" in node_item.code_item.toPlainText()


def test_recipe_search_uses_internal_category_and_recovers_when_cleared(tmp_path):
    _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    editor.category_combo.setCurrentIndex(editor.category_combo.findData("Movement"))
    editor._refresh_recipes("")
    initial_count = editor.recipe_list.count()

    editor.recipe_search.setText("move")
    searched_count = editor.recipe_list.count()
    editor.recipe_search.clear()

    assert initial_count > 0
    assert searched_count > 0
    assert editor.recipe_list.count() == initial_count
