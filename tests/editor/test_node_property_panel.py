"""Every node with authorable properties must show them in the Properties panel.

PHASE 9.5B Stage 4.1.

The reported symptom was that some nodes appear on the canvas but their
properties are absent from the panel, so the only way to configure them is to
hand-edit the ``.zlogic`` JSON. An audit of every runtime executor found the
cause: 26 nodes read properties via ``properties.get(key, default)`` that the
catalogue never declared. What the panel renders comes from the catalogue, so an
undeclared property is an invisible one.

``input_axis`` was the worst case -- its ``negative``/``positive`` key bindings,
probably the most-authored setting in the whole palette, could not be set from
the editor at all.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from engine.logic.node_definitions import NODE_DEFINITIONS  # noqa: E402
from engine.logic.node_system import load_runtime_node_modules  # noqa: E402
from engine.logic.runtime.registry import registry  # noqa: E402

from editor.widgets.logic_graph_editor import LogicGraphEditor  # noqa: E402

#: Properties the runtime resolves itself and the user must not be asked to fill
#: in. Kept explicit so a genuinely missing property cannot hide behind a broad
#: exemption -- see docs/PHASE9_5B_STAGE4_1_NODE_PROPERTIES.md.
INTERNAL_PROPERTIES = {
    "object",        # runtime GameObject handle, resolved from object_name
    "widget",        # runtime widget handle, resolved from widget_name
    "properties",    # add_component: nested component payload
    "inputs",        # call_subgraph: dynamic interface, edited via the graph
    "options",       # show_dialog: list of choices, edited via its own UI
    "default",       # type-dependent, follows the pin type
    "color",         # None means "inherit theme"; declaring it changes behaviour
    "bg_color",
    "fill_color",
    "acceleration",
    "exposed_properties",
    "parameters",
}


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def editor(app):
    instance = LogicGraphEditor()
    yield instance
    instance.deleteLater()


def graph_with(node_type: str) -> dict:
    definition = NODE_DEFINITIONS.get(node_type, {})
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": "PropertyPanel",
        "target": {"type": "name", "value": "Player"},
        "variables": {},
        "nodes": [{
            "id": "n0",
            "type": node_type,
            "title": definition.get("title", node_type),
            "category": definition.get("category", "Custom"),
            "position": [0.0, 0.0],
            "properties": {},
        }],
        "edges": [],
    }


def property_rows(editor) -> list[str]:
    """The property keys the panel is currently showing (minus the title row)."""
    tree = editor.property_tree
    keys = []
    for index in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(index)
        key = item.data(0, 0x0100)  # Qt.UserRole
        if key and key != "title":
            keys.append(str(key))
    return keys


def select_first_node(editor) -> None:
    item = next(iter(editor.node_items.values()))
    editor.scene.clearSelection()
    item.setSelected(True)
    editor._selection_changed()


NODES_WITH_PROPERTIES = sorted(
    node_id for node_id, definition in NODE_DEFINITIONS.items()
    if definition.get("properties")
)

#: One representative per domain -- the golden set from the Stage 4.1 brief.
GOLDEN_NODES = [
    "input_axis", "key_pressed", "move_by", "multiply_number",
    "set_variable", "get_variable", "apply_force", "play_animation",
    "set_ui_text", "play_sound", "load_scene", "show_dialog", "save_game",
]


def test_the_palette_still_has_nodes_with_properties():
    assert len(NODES_WITH_PROPERTIES) > 100, "the sweep below would be vacuous"


@pytest.mark.parametrize("node_type", GOLDEN_NODES)
def test_golden_node_shows_its_properties(editor, node_type):
    if node_type not in NODE_DEFINITIONS:
        pytest.skip(f"{node_type} is not in the current palette")
    editor.set_graph(graph_with(node_type))
    select_first_node(editor)

    shown = property_rows(editor)
    expected = set(NODE_DEFINITIONS[node_type].get("properties", {}))
    expected -= {"exposed_properties", "parameters"}
    assert expected, f"{node_type} declares no properties"
    assert set(shown) >= expected, (
        f"{node_type}: properties missing from the panel: {sorted(expected - set(shown))}"
    )


def test_input_axis_key_bindings_are_authorable(editor):
    """The regression that motivated this stage."""
    editor.set_graph(graph_with("input_axis"))
    select_first_node(editor)
    shown = property_rows(editor)
    assert "negative" in shown and "positive" in shown, (
        "the movement keys are still not editable from the Properties panel"
    )


def test_variable_nodes_expose_name_and_scope(editor):
    for node_type in ("set_variable", "get_variable"):
        editor.set_graph(graph_with(node_type))
        select_first_node(editor)
        shown = property_rows(editor)
        assert "name" in shown, f"{node_type}: the variable name is not editable"
        assert "scope" in shown, f"{node_type}: the variable scope is not editable"


def test_every_property_the_runtime_reads_is_declared():
    """Guards the whole class of bug, not just the nodes fixed by hand."""
    import ast
    import re
    from pathlib import Path

    load_runtime_node_modules()
    root = Path(__file__).resolve().parents[2] / "engine/logic/runtime/nodes"

    invisible: dict[str, list[str]] = {}
    for source_file in sorted(root.glob("*.py")):
        source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            node_ids: list[str] = []
            for decorator in function.decorator_list:
                if isinstance(decorator, ast.Call):
                    for argument in decorator.args:
                        if isinstance(argument, ast.Constant):
                            node_ids.append(argument.value)
                        elif isinstance(argument, (ast.Tuple, ast.List)):
                            node_ids += [
                                element.value for element in argument.elts
                                if isinstance(element, ast.Constant)
                            ]
            if not node_ids:
                continue
            body = ast.get_source_segment(source, function) or ""
            keys = set(re.findall(r"properties\.get\(\s*[\"']([^\"']+)", body))
            for node_id in node_ids:
                declared = set(NODE_DEFINITIONS.get(node_id, {}).get("properties", {}))
                missing = sorted(keys - declared - INTERNAL_PROPERTIES)
                if missing and node_id in NODE_DEFINITIONS:
                    invisible.setdefault(node_id, []).extend(missing)

    assert not invisible, (
        "these nodes read properties the catalogue does not declare, so they "
        f"cannot be set from the Properties panel: {invisible}"
    )


@pytest.mark.parametrize("node_type", NODES_WITH_PROPERTIES)
def test_selecting_any_node_builds_its_panel_without_crashing(editor, node_type):
    """The all-node sweep: no node type may break the Properties panel."""
    editor.set_graph(graph_with(node_type))
    select_first_node(editor)
    shown = property_rows(editor)
    assert isinstance(shown, list)
