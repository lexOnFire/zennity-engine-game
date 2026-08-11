"""Opening and closing graphs repeatedly must not accumulate scene state.

PHASE 9.5B Stage 4.  Stage 3 covered the *runtime* lifecycle; the editor has one
too. Every ``set_graph`` clears the scene and rebuilds it, so a leak here shows
up as QGraphicsItems that survive the clear.
"""

from __future__ import annotations

import gc

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from editor.widgets.logic_graph_editor import LogicGraphEditor  # noqa: E402

from .test_logic_graph_load_complexity import build_graph  # noqa: E402

CYCLES = 20
NODES = 30


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_scene_items_do_not_accumulate_across_reloads(app):
    editor = LogicGraphEditor()
    try:
        editor.set_graph(build_graph(NODES))
        baseline_items = len(editor.scene.items())
        baseline_nodes = len(editor.node_items)
        baseline_edges = len(editor.edge_items)

        for cycle in range(CYCLES):
            editor.set_graph(build_graph(NODES))
            assert len(editor.node_items) == baseline_nodes, f"nodes grew at cycle {cycle}"
            assert len(editor.edge_items) == baseline_edges, f"edges grew at cycle {cycle}"

        assert len(editor.scene.items()) == baseline_items, (
            "QGraphicsItems accumulated across graph reloads"
        )
    finally:
        editor.deleteLater()


def test_reloading_a_graph_releases_the_previous_node_items(app):
    """weakref as detector: the old items must not be reachable afterwards."""
    import weakref

    editor = LogicGraphEditor()
    try:
        editor.set_graph(build_graph(NODES))
        references = [weakref.ref(item) for item in editor.node_items.values()]

        editor.set_graph(build_graph(NODES))
        gc.collect()

        alive = [reference for reference in references if reference() is not None]
        assert not alive, f"{len(alive)} of {len(references)} node items survived the reload"
    finally:
        editor.deleteLater()


def test_switching_between_graphs_of_different_sizes_is_stable(app):
    editor = LogicGraphEditor()
    try:
        for _ in range(5):
            editor.set_graph(build_graph(10))
            small = len(editor.scene.items())
            editor.set_graph(build_graph(40))
            editor.set_graph(build_graph(10))
            assert len(editor.scene.items()) == small, (
                "scene did not return to its smaller size after switching back"
            )
    finally:
        editor.deleteLater()
