"""Suíte de Testes da Plataforma Visual Scripting 2.0 (Production Suite).

Valida o layout de 4 quadrantes, a Mini Live Viewport, os nós tipados e a sincronização do runtime.
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


def test_visual_scripting_2_0_dock_layout(qapp):
    """Valida o layout de 4 áreas e os componentes do Visual Scripting 2.0."""
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock
    from editor.widgets.logic_graph_editor import LogicGraphEditor

    dock = VisualScriptingEditorDock()
    assert isinstance(dock.graph_editor, LogicGraphEditor)
    assert dock.mini_viewport is not None
    assert dock.mini_viewport.transport_toolbar.isHidden()
    assert dock.btn_play is not None
    assert dock.btn_stop is not None


def test_visual_scripting_can_be_a_native_independent_window(qapp):
    from PySide6.QtCore import Qt
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock

    window = VisualScriptingEditorDock()
    window.configure_independent_window()

    assert window.isWindow()
    assert window.windowFlags() & Qt.WindowMinMaxButtonsHint
    assert window.windowFlags() & Qt.WindowCloseButtonHint
    assert window.minimumWidth() >= 960
    assert window.minimumHeight() >= 640


def test_mini_live_viewport_highlight_execution(qapp):
    """Valida o destaque visual de execução da Mini Live Viewport."""
    from editor.visual_scripting.mini_live_viewport import MiniLiveViewportWidget

    viewport = MiniLiveViewportWidget()
    viewport.set_play_mode(True)
    assert viewport.status_badge.text() == "● PLAYING"

    viewport.highlight_execution_node("node_123", "MovePlayer")
    assert viewport.active_node_id == "node_123"
    assert viewport.active_node_name == "MovePlayer"


def test_visual_scripting_dock_runtime_execution_sync(qapp):
    """Valida a sincronização de execução de nós entre o dock e a Mini Live Viewport."""
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock

    dock = VisualScriptingEditorDock()
    dock.highlight_node_execution("n1", "Jump")

    assert dock.mini_viewport.active_node_name == "Jump"
    assert "Jump" in dock.runtime_logs_text.toPlainText()
