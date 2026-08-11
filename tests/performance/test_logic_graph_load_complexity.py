"""Loading a Logic Graph must not be quadratic.

PHASE 9.5B Stage 4.

``LogicNodeItem.itemChange`` called ``refresh_connections()`` on every
``ItemPositionHasChanged``.  That fires once per node placed during a load, and
each refresh walks every edge and every node -- so opening a graph cost O(n^2).
Measured before the fix: 2.5s for 100 nodes, 8.0s for 200, 31.4s for 400, and a
1000-node graph never finished at all.

These tests assert on **call counts and growth ratios**, not milliseconds. A
wall-clock threshold would be a flaky CI gate on shared hardware; the call count
is the invariant that actually encodes the algorithm.
"""

from __future__ import annotations

import time
import uuid

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from editor.widgets.logic_graph_editor import LogicGraphEditor  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def editor(app):
    instance = LogicGraphEditor()
    yield instance
    instance.deleteLater()


def build_graph(node_count: int) -> dict:
    """A wired chain on a grid: distinct positions, so every node really moves."""
    nodes = []
    edges = []
    for index in range(node_count):
        nodes.append({
            "id": f"n{index}",
            "type": "event_update" if index == 0 else "move_by",
            "title": f"Node {index}",
            "category": "Events" if index == 0 else "Movement",
            "position": [float((index % 20) * 260), float((index // 20) * 170)],
            "properties": {},
        })
        if index:
            edges.append({
                "id": uuid.uuid4().hex,
                "from_node": f"n{index - 1}",
                "from_port": "next",
                "to_node": f"n{index}",
                "to_port": "in",
                "kind": "flow",
            })
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": f"Complexity{node_count}",
        "target": {"type": "name", "value": "Player"},
        "variables": {},
        "nodes": nodes,
        "edges": edges,
    }


def load_and_count(editor, node_count: int) -> dict:
    calls = {"refresh": 0, "dirty": 0}
    editor_type = type(editor)
    original_refresh = editor_type.refresh_connections
    original_dirty = editor_type.mark_dirty

    def counting_refresh(self, *args, **kwargs):
        calls["refresh"] += 1
        return original_refresh(self, *args, **kwargs)

    def counting_dirty(self, *args, **kwargs):
        calls["dirty"] += 1
        return original_dirty(self, *args, **kwargs)

    editor_type.refresh_connections = counting_refresh
    editor_type.mark_dirty = counting_dirty
    try:
        started = time.perf_counter()
        editor.set_graph(build_graph(node_count))
        calls["seconds"] = time.perf_counter() - started
    finally:
        editor_type.refresh_connections = original_refresh
        editor_type.mark_dirty = original_dirty
    return calls


@pytest.mark.parametrize("node_count", [10, 100, 200])
def test_connection_refresh_count_is_constant(editor, node_count):
    """The invariant: refreshes must not scale with the number of nodes."""
    calls = load_and_count(editor, node_count)
    assert calls["refresh"] <= 4, (
        f"{calls['refresh']} connection refreshes for {node_count} nodes; "
        "this used to be one per node, which is what made loading quadratic"
    )


def test_opening_a_graph_does_not_mark_it_dirty(editor):
    """Placing nodes used to call mark_dirty(), so opening a file dirtied it."""
    calls = load_and_count(editor, 50)
    assert calls["dirty"] == 0
    assert editor._dirty is False


def test_load_time_grows_roughly_linearly(editor):
    """Doubling the nodes must not roughly quadruple the time.

    Generous ceiling on purpose: the point is to catch a return to quadratic
    behaviour (~4x per doubling), not to police normal variance. Measured after
    the fix: 2.09x, 2.37x and 2.35x per doubling.
    """
    small = load_and_count(editor, 100)["seconds"]
    large = load_and_count(editor, 200)["seconds"]

    if small < 0.05:
        pytest.skip("load too fast to compare reliably on this machine")

    ratio = large / small
    assert ratio < 3.2, (
        f"doubling nodes multiplied load time by {ratio:.2f}x; "
        "quadratic behaviour has returned"
    )


def test_all_edges_are_still_rendered(editor):
    """Correctness gate: the optimisation must not skip connections."""
    node_count = 100
    editor.set_graph(build_graph(node_count))
    assert len(editor.node_items) == node_count
    assert len(editor.edge_items) == node_count - 1, (
        "edges are missing after a bulk load; the deferred refresh did not run"
    )


def test_nested_bulk_updates_refresh_once(editor):
    """Only the outermost block refreshes, and it must actually refresh."""
    editor.set_graph(build_graph(10))
    editor_type = type(editor)
    original = editor_type.refresh_connections
    count = {"n": 0}

    def counting(self, *args, **kwargs):
        count["n"] += 1
        return original(self, *args, **kwargs)

    editor_type.refresh_connections = counting
    try:
        with editor.bulk_update():
            with editor.bulk_update():
                editor.request_connection_refresh()
                editor.request_connection_refresh()
            assert count["n"] == 0, "an inner block refreshed early"
        assert count["n"] == 1, "the outer block did not refresh on exit"
    finally:
        editor_type.refresh_connections = original


def test_request_refresh_outside_bulk_is_immediate(editor):
    editor.set_graph(build_graph(5))
    assert editor.is_bulk_updating is False
    editor.request_connection_refresh()  # must not raise or defer
