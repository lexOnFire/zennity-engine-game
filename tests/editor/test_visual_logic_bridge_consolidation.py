from editor.runtime.visual_scripting_bridge import VisualLogicBridge, VisualScriptingBridge
from editor.widgets.logic_graph_editor import LogicGraphEditor
from PySide6.QtWidgets import QApplication


class _Context:
    selection = None


def test_visual_logic_bridge_is_the_single_owner_of_mode_bridges():
    bridge = VisualLogicBridge(_Context())
    behavior = bridge.mode_bridge("behavior_tree")
    assert behavior is bridge.mode_bridge("behavior_tree")
    assert bridge.mode_bridge("dialogue") is not behavior
    assert VisualScriptingBridge is VisualLogicBridge


def test_official_logic_editor_emits_bridge_events():
    QApplication.instance() or QApplication([])
    editor = LogicGraphEditor()
    added = []
    selected = []
    editor.node_added.connect(added.append)
    editor.node_selected.connect(selected.append)

    palette_item = editor.palette.item(0)
    editor._add_palette_item(palette_item)
    assert added

    node_item = next(iter(editor.node_items.values()))
    node_item.setSelected(True)
    editor._selection_changed()
    assert selected[-1] is node_item.node
