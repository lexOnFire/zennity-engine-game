"""Suíte de Testes dos Recursos Inovadores: Runtime Explain Mode & Data Flow Visualization.

Valida a explicação de causas de comportamento e a animação do fluxo de mutação de dados.
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


class FakeObject:
    def __init__(self):
        self.name = "PlayerHero"
        self.velocity = [4.2, 0.0]
        self.state = "RUNNING"


def test_runtime_explain_mode_explanation():
    """Valida a geração de explicação da causa raiz pelo Runtime Explain Mode (Sprint 9)."""
    from editor.visual_scripting.runtime_explain_mode import RuntimeExplainMode

    explain_mode = RuntimeExplainMode.instance()
    player = FakeObject()

    exp = explain_mode.explain_object_behavior(player, active_node_name="Move")
    assert exp["object_name"] == "PlayerHero"
    assert exp["triggering_node"] == "Move"
    assert "Move" in exp["cause_summary"]
    assert len(exp["execution_chain"]) == 4


def test_data_flow_visualization_animator():
    """Valida a animação do trajeto de mutação de dados (Sprint 10)."""
    from editor.visual_scripting.data_flow_animator import DataFlowVisualizationAnimator

    animator = DataFlowVisualizationAnimator()
    animator.trigger_variable_flow("speed", "Move()", 4.2)

    assert len(animator.active_flows) == 1
    assert animator.active_flows[0]["var_name"] == "speed"
    assert animator.active_flows[0]["value"] == "4.2"


def test_visual_scripting_dock_explain_trigger(qapp):
    """Valida o acionamento do Explain Mode no VisualScriptingEditorDock."""
    from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock

    dock = VisualScriptingEditorDock()
    dock.trigger_explain_mode()

    logs = dock.runtime_logs_text.toPlainText()
    assert "[EXPLAIN]" in logs
    assert "Move" in logs
