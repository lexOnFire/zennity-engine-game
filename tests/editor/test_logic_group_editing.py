import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from editor.widgets.logic_graph_editor import LogicGraphEditor
from editor.widgets.logic_graph.group_item import LogicGroupItem


def _app():
    return QApplication.instance() or QApplication([])


def test_logic_group_can_be_selected_renamed_and_recolored() -> None:
    _app()
    editor = LogicGraphEditor()
    group_data = {"id": "grp_1", "title": "Untitled Group", "position": [100.0, 100.0], "size": [300.0, 200.0], "color": "#2d3545"}
    group_item = LogicGroupItem(editor, group_data)
    editor.scene.addItem(group_item)

    group_item.setSelected(True)
    editor._selection_changed()

    assert "Untitled Group" in editor.selected_label.text()
    assert editor.property_tree.topLevelItemCount() == 2

    title_item = editor.property_tree.topLevelItem(0)
    title_item.setText(1, "Player Movement Group")
    editor._property_changed(title_item, 1)

    assert group_data["title"] == "Player Movement Group"
    assert group_item.title_item.toPlainText() == "Player Movement Group"
