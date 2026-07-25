"""Suíte de Testes da Camada Runtime Visualization Panel & Visual Debugger AAA.

Valida a renderização de gizmos visuais de física/IA/força, o buffer de Replay dos últimos 5s,
a interatividade de seleção e o gradiente do Node Performance Heat Map.
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


def test_runtime_visualization_renderer_instantiation():
    """Valida o renderizador de Gizmos internos da Viewport."""
    from editor.visual_scripting.runtime_visualization import RuntimeVisualizationRenderer

    renderer = RuntimeVisualizationRenderer()
    assert renderer.show_colliders is True
    assert renderer.show_velocity is True
    assert renderer.show_forces is True
    assert renderer.show_ai_fov is True


def test_runtime_visualization_panel_replay_buffer(qapp):
    """Valida o buffer circular de Replay dos últimos 5 segundos."""
    from editor.visual_scripting.mini_live_viewport import RuntimeVisualizationPanelWidget

    panel = RuntimeVisualizationPanelWidget()
    panel.highlight_execution_node("n_move", "Move")
    panel._on_tick()

    assert len(panel.replay_buffer) >= 1
    assert panel.replay_buffer[-1]["node_name"] == "Move"

    # Simula retrocesso no Replay (Frame 0)
    panel.set_replay_frame(0)
    assert panel.is_replaying is True
    assert "REPLAY" in panel.status_badge.text()

    # Retorna ao vivo (Live Mode)
    panel.resume_live()
    assert panel.is_replaying is False


def test_node_performance_heat_map(qapp):
    """Valida o cálculo do gradiente térmico de execuções do nó (Node Performance Heat Map)."""
    from engine.core.metadata.node import NodeDefinition
    from editor.widgets.graph_editor.node_item import GraphNodeItem

    node_def = NodeDefinition(id="test_node", name_key="Test Node", category_key="logic.category.movement")
    node_item = GraphNodeItem(node_def, {"id": "n1", "position": [0, 0]})

    # Simula execuções frequentes
    for _ in range(60):
        node_item.record_execution()

    assert node_item.execution_count == 60
    # Deve atingir o nível Laranja / Quente (> 50 execuções)
    assert node_item.pen().color().name() in ["#ff9933", "#ff4d4d"]
