"""Testes da Fase 8.1 — Migração do Inspector e Viewport para o Framework 2.0.

Valida:
  - Inspector utiliza PropertyBindingGroup para gerenciar propriedades do objeto.
  - Alterações no Inspector disparam eventos no EventBus no domínio Scene.*.
  - Sincronização entre SelectionService -> Inspector -> PropertyBinding -> Undo/Redo -> EventBus.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


class FakeGameObject:
    def __init__(self, name: str = "Player"):
        self.name = name
        self.active = True
        self.id = f"id_{name.lower()}"
        self.components: list = []


def test_inspector_uses_property_binding_group():
    """Inspector cria e usa PropertyBindingGroup ao carregar um objeto."""
    from editor.premium_inspector_panel import RealInspectorPanel
    from editor.runtime.command_manager import CommandManager

    # Instancia o painel e o gerenciador de comandos
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível neste ambiente")

    cm = CommandManager()
    panel = RealInspectorPanel()
    panel.set_command_manager(cm)

    obj = FakeGameObject("Hero")
    panel.load_object(obj)

    assert hasattr(panel, "binding_group")
    assert panel.binding_group is not None

    # Altera propriedade via binding_group
    panel.binding_group.set("name", "SuperHero")
    assert obj.name == "SuperHero"
    assert cm.can_undo

    # Desfaz alteração via CommandManager
    cm.undo()
    assert obj.name == "Hero"


def test_inspector_property_change_emits_scene_event():
    """Alteração via PropertyBinding no Inspector emite evento Scene.object_modified."""
    from editor.premium_inspector_panel import RealInspectorPanel
    from editor.core.event_bus import EventBus, EVENT_OBJECT_MODIFIED

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível neste ambiente")

    panel = RealInspectorPanel()
    obj = FakeGameObject("Enemy")
    panel.load_object(obj)

    events_received = []
    EventBus.subscribe(EVENT_OBJECT_MODIFIED, lambda **kw: events_received.append(kw))

    panel.binding_group.set("name", "BossEnemy", record_undo=False)

    assert len(events_received) >= 1
    assert events_received[-1]["property"] == "name"
    assert events_received[-1]["value"] == "BossEnemy"
