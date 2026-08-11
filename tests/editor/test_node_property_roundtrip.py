"""A property edited in the panel must survive save, close and reopen.

PHASE 9.5B Stage 4.1. Persistence is only half the contract -- the runtime has
to read the same value back, which is covered in
``tests/logic/test_node_property_runtime_contract.py``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from engine.logic.graph_asset import load_logic_graph, save_logic_graph  # noqa: E402
from engine.logic.node_definitions import NODE_DEFINITIONS  # noqa: E402

from editor.widgets.logic_graph_editor import LogicGraphEditor  # noqa: E402

from .test_node_property_panel import graph_with, select_first_node  # noqa: E402

#: One value per Python type the catalogue actually uses.
TYPE_SAMPLES = [
    ("input_axis", "positive", "K"),          # str
    ("input_axis", "negative", "J"),          # str
    ("sequence", "outputs", 5),               # int
    ("move_by", "x", -42.5),                  # float
    ("clone_object", "use_pool", True),       # bool
    ("start_texture_scroll", "repeat_x", True),
    ("start_texture_scroll", "parallax", 0.25),
    ("set_variable", "name", "player_health"),
    ("set_variable", "scope", "global"),
    ("find_tag", "tag", "Enemy"),
    ("set_ui_text", "widget_name", "ScoreLabel"),
    ("load_game", "slot", "slot3"),
]


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def editor(app):
    instance = LogicGraphEditor()
    yield instance
    instance.deleteLater()


@pytest.mark.parametrize("node_type,key,value", TYPE_SAMPLES)
def test_property_survives_save_and_reopen(editor, tmp_path, node_type, key, value):
    if node_type not in NODE_DEFINITIONS:
        pytest.skip(f"{node_type} is not in the current palette")

    editor.set_graph(graph_with(node_type))
    node = editor.graph["nodes"][0]
    node["properties"][key] = value

    destination = tmp_path / f"{node_type}_{key}.zlogic"
    save_logic_graph(destination, editor.graph)

    reopened = load_logic_graph(destination)
    stored = reopened["nodes"][0]["properties"][key]

    assert stored == value, f"{node_type}.{key}: {stored!r} != {value!r}"
    assert type(stored) is type(value), (
        f"{node_type}.{key}: type changed on roundtrip, "
        f"{type(value).__name__} -> {type(stored).__name__}"
    )

    # And the editor loads it back as the same value.
    editor.set_graph(reopened, path=destination)
    assert editor.graph["nodes"][0]["properties"][key] == value


def test_defaults_are_materialized_on_load(editor, tmp_path):
    """A node saved with no properties still gets its declared defaults back."""
    editor.set_graph(graph_with("input_axis"))
    destination = tmp_path / "defaults.zlogic"
    save_logic_graph(destination, editor.graph)

    editor.set_graph(load_logic_graph(destination), path=destination)
    select_first_node(editor)

    properties = editor.graph["nodes"][0]["properties"]
    assert properties.get("negative") == "A"
    assert properties.get("positive") == "D"


def test_non_default_values_are_not_overwritten_by_defaults(editor, tmp_path):
    """The seeding must fill gaps, never clobber what the user authored."""
    editor.set_graph(graph_with("input_axis"))
    editor.graph["nodes"][0]["properties"].update({"negative": "LEFT", "positive": "RIGHT"})

    destination = tmp_path / "authored.zlogic"
    save_logic_graph(destination, editor.graph)
    editor.set_graph(load_logic_graph(destination), path=destination)
    select_first_node(editor)

    properties = editor.graph["nodes"][0]["properties"]
    assert properties["negative"] == "LEFT"
    assert properties["positive"] == "RIGHT"
