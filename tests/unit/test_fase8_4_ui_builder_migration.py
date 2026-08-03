"""Testes específicos do UI Builder integrado ao Editor Framework 2.0 (Fase 8.4).
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_ui_builder_bridge_registers_tool():
    """UIBuilderBridge registra 'ui.builder' no ToolRegistry."""
    from editor.runtime.ui_builder_bridge import UIBuilderBridge
    from editor.workspace.tool_registry import ToolRegistry

    class FakeCtx:
        pass

    ctx = FakeCtx()
    bridge = UIBuilderBridge(ctx)

    tool = ToolRegistry.instance().get("ui.builder")
    assert tool is not None
    assert tool.id == "ui.builder"
    assert "ui.add_widget" in tool.commands
    assert "Ctrl+Shift+U" in tool.shortcuts


def test_ui_builder_dock_emits_event():
    """UIBuilderDock.add_widget() emite evento UI.widget_added via EventBus."""
    from editor.ui_builder.ui_builder_dock import UIBuilderDock
    from engine.ui.runtime import UIButton
    from editor.core.event_bus import EventBus

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível")

    dock = UIBuilderDock()
    events = []
    EventBus.subscribe("UI.widget_added", lambda **kw: events.append(kw))

    dock.add_widget(UIButton("BtnTest"))

    assert len(events) >= 1
    assert events[-1]["widget"].name == "BtnTest"
