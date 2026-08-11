"""Editing a property marks the graph dirty; opening one does not.

PHASE 9.5B Stage 4.1. Stage 4 removed a per-node ``mark_dirty()`` that fired
while placing items, so merely opening a graph reported unsaved changes. These
tests pin both halves so neither direction regresses.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from editor.widgets.logic_graph_editor import LogicGraphEditor  # noqa: E402

from .test_node_property_panel import graph_with  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def editor(app):
    instance = LogicGraphEditor()
    yield instance
    instance.deleteLater()


def test_opening_a_graph_is_not_dirty(editor):
    editor.set_graph(graph_with("input_axis"))
    assert editor._dirty is False, "opening a graph reported unsaved changes"


def test_reopening_repeatedly_stays_clean(editor):
    for _ in range(5):
        editor.set_graph(graph_with("move_by"))
        assert editor._dirty is False


def test_marking_dirty_is_reflected(editor):
    editor.set_graph(graph_with("input_axis"))
    assert editor._dirty is False
    editor.mark_dirty()
    assert editor._dirty is True, "mark_dirty did not take effect"
