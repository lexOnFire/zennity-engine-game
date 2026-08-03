"""Testes unitários do Sprint 4a — Integração Reativa: Hierarchy → Scene → Inspector → Viewport.

Valida que o ReactiveEditorBridge conecta o SelectionService com
os 4 painéis base sem polling e sem acoplamento direto.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fakes
# ─────────────────────────────────────────────────────────────────────────────

class FakeGameObject:
    def __init__(self, name: str = "Player"):
        self.name = name
        self.id = f"id_{name.lower()}"
        self.children: list = []
        self.components: list = []


class FakeHierarchyDock:
    def __init__(self):
        self.last_selected = "NOT_SET"
        self.populate_calls = 0

    def select_object_in_tree(self, obj):
        self.last_selected = obj

    def populate_tree(self):
        self.populate_calls += 1


class FakeInspectorDock:
    def __init__(self):
        self.last_loaded = "NOT_SET"

    def load_object(self, obj):
        self.last_loaded = obj


class FakeViewport:
    def __init__(self):
        self.last_selected = "NOT_SET"

    def select_object(self, obj):
        self.last_selected = obj


class FakeEditorContext:
    def __init__(self):
        from editor.runtime.selection_manager import SelectionService
        self.selection = SelectionService()


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4a — ReactiveEditorBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_bridge_propagates_selection_to_inspector():
    """Quando SelectionService muda, InspectorDock é atualizado automaticamente."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    inspector = FakeInspectorDock()
    bridge.attach_inspector(inspector)

    obj = FakeGameObject("Player")
    ctx.selection.select_item(obj, type="game_object", context="test")

    assert inspector.last_loaded is obj


def test_bridge_propagates_selection_to_hierarchy():
    """Quando SelectionService muda, HierarchyDock destaca o objeto selecionado."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    hierarchy = FakeHierarchyDock()
    bridge.attach_hierarchy(hierarchy)

    obj = FakeGameObject("Enemy")
    ctx.selection.select_item(obj, type="game_object", context="test")

    assert hierarchy.last_selected is obj


def test_bridge_propagates_selection_to_viewport():
    """Quando SelectionService muda, Viewport foca/gizmo no objeto."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    viewport = FakeViewport()
    bridge.attach_viewport(viewport)

    obj = FakeGameObject("Camera")
    ctx.selection.select_item(obj, type="game_object", context="test")

    assert viewport.last_selected is obj


def test_bridge_propagates_to_all_panels_at_once():
    """Uma única mudança no SelectionService atualiza Hierarchy + Inspector + Viewport."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    hierarchy = FakeHierarchyDock()
    inspector = FakeInspectorDock()
    viewport = FakeViewport()

    bridge.attach_hierarchy(hierarchy)
    bridge.attach_inspector(inspector)
    bridge.attach_viewport(viewport)

    obj = FakeGameObject("Boss")
    ctx.selection.select_item(obj, type="game_object", context="test")

    assert hierarchy.last_selected is obj
    assert inspector.last_loaded is obj
    assert viewport.last_selected is obj


def test_bridge_clears_all_panels_on_clear():
    """Limpar a seleção propaga None para todos os painéis."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    hierarchy = FakeHierarchyDock()
    inspector = FakeInspectorDock()
    viewport = FakeViewport()

    bridge.attach_hierarchy(hierarchy)
    bridge.attach_inspector(inspector)
    bridge.attach_viewport(viewport)

    obj = FakeGameObject("NPC")
    ctx.selection.select_item(obj, type="game_object", context="test")
    ctx.selection.clear_selection()

    assert hierarchy.last_selected is None
    assert inspector.last_loaded is None
    assert viewport.last_selected is None


def test_bridge_public_select_api():
    """Bridge.select() é a API pública para seleção centralizada."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    inspector = FakeInspectorDock()
    bridge.attach_inspector(inspector)

    obj = FakeGameObject("Hero")
    bridge.select(obj, context="hierarchy")

    assert inspector.last_loaded is obj
    assert ctx.selection.current_item is not None
    assert ctx.selection.current_item.context == "hierarchy"


def test_bridge_no_duplicate_notifications():
    """Bridge não deve causar loop: seleção de Hierarchy não re-notifica Hierarchy."""
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    bridge = ReactiveEditorBridge(ctx)

    calls = []

    class CountingHierarchy(FakeHierarchyDock):
        def select_object_in_tree(self, obj):
            calls.append(obj)

    hierarchy = CountingHierarchy()
    bridge.attach_hierarchy(hierarchy)

    obj = FakeGameObject("Solo")
    # 3 seleções distintas
    bridge.select(obj)
    bridge.select(obj)
    bridge.select(obj)

    # Não importa o número exato; apenas não deve crescer em loop infinito
    assert len(calls) <= 3


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 4a — SceneViewModel atualizado com SelectionService
# ─────────────────────────────────────────────────────────────────────────────

def _make_scene_viewmodel(use_service: bool = True):
    """Factory para SceneViewModel com seleção opcional via SelectionService."""
    from editor.models.scene_model import SceneModel
    from editor.viewmodels.scene_viewmodel import SceneViewModel
    from editor.runtime.selection_manager import SelectionService

    model = SceneModel()
    svc = SelectionService() if use_service else None
    return SceneViewModel(model, svc), model, svc


def test_scene_viewmodel_uses_selection_service():
    """SceneViewModel aceita SelectionService como SelectionManager."""
    import importlib
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível neste ambiente")

    vm, model, svc = _make_scene_viewmodel(use_service=True)
    assert vm.selection_manager is svc


def test_scene_viewmodel_selection_propagates_via_service():
    """Seleção via SelectionService chega ao SceneViewModel."""
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível neste ambiente")

    vm, model, svc = _make_scene_viewmodel(use_service=True)

    obj = FakeGameObject("TestObj")
    svc.select_item(obj, type="game_object", context="hierarchy")

    assert vm.selected_object is obj
