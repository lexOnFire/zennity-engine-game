"""Suíte de Testes da Camada Bidirectional Debug Engine & Runtime Inspector Dual.

Valida a sincronização bidirecional de seleção (Graph <-> Viewport), o Inspector Dual
separando propriedades salvas de métricas voláteis de runtime e a comutação das Visual Debug Layers.
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


class FakeGameObject:
    def __init__(self, name: str = "EnemyHero"):
        self.name = name
        self.id = "id_enemy_123"
        self.active = True
        self.velocity = [3.5, 0.0]
        self.is_grounded = True
        self.health = 100.0
        self.state = "PATROL"


def test_bidirectional_debug_bridge_registration():
    """Valida a vinculação simétrica de nós e objetos de jogo no BidirectionalDebugBridge."""
    from editor.runtime.bidirectional_debug_bridge import BidirectionalDebugBridge

    bridge = BidirectionalDebugBridge.instance()
    enemy = FakeGameObject("BossEnemy")

    bridge.register_binding("node_attack_45", enemy)
    assert bridge._node_to_object_map["node_attack_45"] is enemy
    assert bridge._object_to_node_map[enemy.id] == "node_attack_45"


def test_runtime_inspector_dual_section(qapp):
    """Valida a renderização da seção dividida de Dados de Runtime no RealInspectorPanel."""
    from editor.premium_inspector_panel import RealInspectorPanel

    panel = RealInspectorPanel()
    enemy = FakeGameObject("Hero")
    panel.load_object(enemy)

    assert panel.current_object is enemy
    assert hasattr(panel, "_render_runtime_inspector_section")


def test_visual_debug_layers_toggles(qapp):
    """Valida a comutação das camadas visuais de diagnósticos no Runtime Visualization Panel."""
    from editor.visual_scripting.mini_live_viewport import RuntimeVisualizationPanelWidget

    panel = RuntimeVisualizationPanelWidget()
    assert panel.chk_phys.isChecked() is True
    assert panel.chk_nav.isChecked() is True
    assert panel.chk_ai.isChecked() is True

    # Desativa a camada de física
    panel.chk_phys.setChecked(False)
    assert panel.renderer.show_colliders is False
