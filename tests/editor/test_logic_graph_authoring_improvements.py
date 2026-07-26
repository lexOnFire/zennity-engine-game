import json

from PySide6.QtWidgets import QApplication

from editor.widgets.logic_graph_editor import LogicGraphEditor
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
