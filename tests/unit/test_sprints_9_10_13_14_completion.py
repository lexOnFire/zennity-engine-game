"""Suíte de Testes para o Fechamento dos Sprints 9, 10, 13 e 14.

Valida a Runtime Timeline (Sprint 13) e o Subgraph / Macro Manager (Sprint 14).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_runtime_timeline_widget_snapshot(qapp):
    """Valida o registro e navegação de frames na Runtime Timeline (Sprint 13)."""
    from editor.visual_scripting.runtime_timeline import RuntimeTimelineWidget

    timeline = RuntimeTimelineWidget()
    timeline.record_frame_snapshot(143, "Move", ["CollisionEnter"], {"speed": 3.5})

    assert len(timeline.recorded_frames) == 1
    assert timeline.recorded_frames[0]["frame"] == 143
    assert timeline.recorded_frames[0]["node_name"] == "Move"


def test_subgraph_and_macro_manager():
    """Valida o empacotamento e expansão de Subgrafos e Macros (Sprint 14)."""
    from editor.visual_scripting.subgraphs_framework import SubgraphNodeManager

    mgr = SubgraphNodeManager()
    inner_nodes = [{"id": "n1", "type": "move"}, {"id": "n2", "type": "jump"}]
    macro = mgr.create_subgraph_node("PlayerMovementMacro", inner_nodes)

    assert macro["title"] == "PlayerMovementMacro"
    assert len(macro["inner_nodes"]) == 2

    expanded = mgr.expand_subgraph(macro["id"])
    assert len(expanded) == 2
    assert expanded[0]["id"] == "n1"


def test_visual_scripting_dock_timeline_tab(qapp):
    """Valida a inclusão da aba Runtime Timeline no VisualScriptingEditorDock."""
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock

    dock = VisualScriptingEditorDock()
    assert hasattr(dock, "runtime_timeline")
    assert dock.watches_tabs.count() >= 2
