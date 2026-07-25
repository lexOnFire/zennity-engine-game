"""Testes unitários do Sprint 4b — Animation Studio + Visual Scripting integrados ao Framework 2.0.

Valida:
  - AnimationStudioBridge: EventBus Animation.*, DocumentManager, ToolRegistry
  - VisualScriptingBridge: EventBus Graph.*, DocumentManager, ToolRegistry
  - EditorBridgeOrchestrator: setup completo em uma única chamada
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Fakes
# ─────────────────────────────────────────────────────────────────────────────

class FakeEditorContext:
    def __init__(self):
        from editor.runtime.selection_manager import SelectionService
        self.selection = SelectionService()


class FakeAnimationDock:
    """Simulação mínima do AnimationStudioDock para testes sem Qt."""
    def __init__(self):
        self._play_callbacks = []
        self._pause_callbacks = []
        self._stop_callbacks = []
        self._hot_reload_callbacks = []

    def simulate_play(self):
        for cb in self._play_callbacks:
            cb()

    def simulate_stop(self):
        for cb in self._stop_callbacks:
            cb()

    def simulate_hot_reload(self):
        for cb in self._hot_reload_callbacks:
            cb()


class FakeVisualScriptingDock:
    """Simulação mínima do VisualScriptingEditorDock para testes sem Qt."""
    def __init__(self):
        self.graph_editor = FakeGraphEditor()


class FakeGraphEditor:
    def __init__(self):
        self._node_selected_handlers = []

    def simulate_node_selected(self, node):
        for h in self._node_selected_handlers:
            h(node)

    def connect_node_selected(self, handler):
        self._node_selected_handlers.append(handler)


class FakeNode:
    def __init__(self, node_id="node_001", label="Start"):
        self.node_id = node_id
        self.label = label


class FakeHierarchy:
    def __init__(self):
        self.last_selected = "NOT_SET"

    def select_object_in_tree(self, obj):
        self.last_selected = obj


class FakeInspector:
    def __init__(self):
        self.last_loaded = "NOT_SET"

    def load_object(self, obj):
        self.last_loaded = obj


class FakeViewport:
    def __init__(self):
        self.last_selected = "NOT_SET"

    def select_object(self, obj):
        self.last_selected = obj


# ─────────────────────────────────────────────────────────────────────────────
# AnimationStudioBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_animation_bridge_registers_tool():
    """AnimationStudioBridge registra 'animation.studio' no ToolRegistry."""
    from editor.runtime.animation_studio_bridge import AnimationStudioBridge
    from editor.workspace.tool_registry import ToolRegistry

    # Limpa estado para isolar o teste
    registry = ToolRegistry()

    ctx = FakeEditorContext()
    bridge = AnimationStudioBridge(ctx)

    # O bridge usa ToolRegistry.instance() que é singleton
    tool = ToolRegistry.instance().get("animation.studio")
    assert tool is not None
    assert tool.id == "animation.studio"
    assert "animation.play" in tool.commands
    assert "Ctrl+Shift+A" in tool.shortcuts
    assert tool.menu == "Ferramentas"


def test_animation_bridge_open_document():
    """AnimationStudioBridge abre documento .zanim no DocumentManager."""
    from editor.runtime.animation_studio_bridge import AnimationStudioBridge
    from editor.workspace.document_framework import DocumentManager, DocumentType

    # Cria DocumentManager isolado para o teste
    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    bridge = AnimationStudioBridge(ctx)

    doc = bridge.open_animation_document(path="anims/player_walk.zanim")

    assert doc is not None
    assert doc.doc_type == DocumentType.ANIMATION
    assert doc.path is not None
    assert "player_walk" in str(doc.path)

    DocumentManager._instance = None  # cleanup


def test_animation_bridge_emits_playback_event():
    """AnimationStudioBridge emite Animation.playback_changed via EventBus."""
    from editor.runtime.animation_studio_bridge import AnimationStudioBridge
    from editor.core.event_bus import EventBus, EVENT_ANIMATION_PLAYBACK

    ctx = FakeEditorContext()
    bridge = AnimationStudioBridge(ctx)

    received = []
    EventBus.subscribe(EVENT_ANIMATION_PLAYBACK, lambda **kw: received.append(kw))

    bridge._emit_playback("playing")
    bridge._emit_playback("stopped")

    assert any(r.get("state") == "playing" for r in received)
    assert any(r.get("state") == "stopped" for r in received)


def test_animation_bridge_add_keyframe_emits_event():
    """add_keyframe emite Animation.keyframe_changed e marca documento como modificado."""
    from editor.runtime.animation_studio_bridge import AnimationStudioBridge
    from editor.workspace.document_framework import DocumentManager, DocumentType
    from editor.core.event_bus import EventBus, EVENT_ANIMATION_KEYFRAME

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    bridge = AnimationStudioBridge(ctx)
    bridge.open_animation_document(path="test.zanim")

    received = []
    EventBus.subscribe(EVENT_ANIMATION_KEYFRAME, lambda **kw: received.append(kw))

    bridge.add_keyframe("Transform", 1.5, {"x": 10.0})

    assert len(received) >= 1
    assert received[-1]["track"] == "Transform"
    assert received[-1]["time"] == 1.5
    assert bridge._current_document.is_modified

    DocumentManager._instance = None


def test_animation_bridge_add_track_emits_event():
    """add_track emite Animation.track_changed."""
    from editor.runtime.animation_studio_bridge import AnimationStudioBridge
    from editor.workspace.document_framework import DocumentManager
    from editor.core.event_bus import EventBus, EVENT_ANIMATION_TRACK

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    bridge = AnimationStudioBridge(ctx)
    bridge.open_animation_document(path="test.zanim")

    received = []
    EventBus.subscribe(EVENT_ANIMATION_TRACK, lambda **kw: received.append(kw))

    bridge.add_track("Color")

    assert any(r.get("track") == "Color" and r.get("action") == "added" for r in received)

    DocumentManager._instance = None


# ─────────────────────────────────────────────────────────────────────────────
# VisualScriptingBridge
# ─────────────────────────────────────────────────────────────────────────────

def test_visual_scripting_bridge_registers_tool():
    """VisualScriptingBridge registra 'visual_scripting.editor' no ToolRegistry."""
    from editor.runtime.visual_scripting_bridge import VisualScriptingBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = VisualScriptingBridge(ctx)

    tool = ToolRegistry.instance().get("visual_scripting.editor")
    assert tool is not None
    assert tool.id == "visual_scripting.editor"
    assert "graph.add_node" in tool.commands
    assert "Ctrl+Shift+L" in tool.shortcuts


def test_visual_scripting_bridge_open_document():
    """VisualScriptingBridge abre documento .zvs no DocumentManager."""
    from editor.runtime.visual_scripting_bridge import VisualScriptingBridge
    from editor.workspace.document_framework import DocumentManager, DocumentType

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    bridge = VisualScriptingBridge(ctx)

    doc = bridge.open_script_document(path="scripts/player_logic.zvs")

    assert doc is not None
    assert doc.doc_type == DocumentType.VISUAL_SCRIPT
    assert "player_logic" in str(doc.path)

    DocumentManager._instance = None


def test_visual_scripting_bridge_node_selection_propagates_to_inspector():
    """Nó selecionado no Visual Scripting propaga para Inspector via SelectionService."""
    from editor.runtime.visual_scripting_bridge import VisualScriptingBridge
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    reactive = ReactiveEditorBridge(ctx)
    inspector = FakeInspector()
    reactive.attach_inspector(inspector)

    bridge = VisualScriptingBridge(ctx)
    bridge.attach_reactive_bridge(reactive)

    node = FakeNode("node_start", "Start")
    # Simula seleção de nó via SelectionService (como o bridge real faria)
    ctx.selection.select_item(node, type="node", context="visual_scripting", id="node_start")

    assert inspector.last_loaded is node


def test_visual_scripting_bridge_add_node_emits_event():
    """add_node() emite Graph.node_added via EventBus."""
    from editor.runtime.visual_scripting_bridge import VisualScriptingBridge
    from editor.workspace.document_framework import DocumentManager
    from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_ADDED

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    bridge = VisualScriptingBridge(ctx)
    bridge.open_script_document(path="test_script.zvs")

    received = []
    EventBus.subscribe(EVENT_GRAPH_NODE_ADDED, lambda **kw: received.append(kw))

    bridge.add_node("ConditionNode", position=(100, 200))

    assert any(r.get("node_type") == "ConditionNode" for r in received)
    assert bridge._current_document.is_modified

    DocumentManager._instance = None


# ─────────────────────────────────────────────────────────────────────────────
# EditorBridgeOrchestrator
# ─────────────────────────────────────────────────────────────────────────────

def test_orchestrator_setup_creates_all_bridges():
    """EditorBridgeOrchestrator cria ReactiveEditorBridge + AnimationStudioBridge + VisualScriptingBridge."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)

    hierarchy = FakeHierarchy()
    inspector = FakeInspector()
    viewport = FakeViewport()

    orchestrator.setup(
        hierarchy=hierarchy,
        inspector=inspector,
        viewport=viewport,
    )

    assert orchestrator.reactive is not None
    assert orchestrator.animation is not None
    assert orchestrator.visual_scripting is not None


def test_orchestrator_select_propagates_to_all_panels():
    """Orchestrator.select() propaga a seleção para Hierarchy + Inspector + Viewport."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)

    hierarchy = FakeHierarchy()
    inspector = FakeInspector()
    viewport = FakeViewport()

    orchestrator.setup(hierarchy=hierarchy, inspector=inspector, viewport=viewport)

    class FakeObj:
        name = "Dragon"

    obj = FakeObj()
    orchestrator.select(obj, context="hierarchy")

    assert hierarchy.last_selected is obj
    assert inspector.last_loaded is obj
    assert viewport.last_selected is obj


def test_orchestrator_open_animation_returns_document():
    """Orchestrator.open_animation() retorna EditorDocument do tipo ANIMATION."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentManager, DocumentType

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    doc = orchestrator.open_animation(path="anims/dragon_fly.zanim")

    assert doc is not None
    assert doc.doc_type == DocumentType.ANIMATION

    DocumentManager._instance = None


def test_orchestrator_open_visual_script_returns_document():
    """Orchestrator.open_visual_script() retorna EditorDocument do tipo VISUAL_SCRIPT."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentManager, DocumentType

    mgr = DocumentManager()
    DocumentManager._instance = mgr

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    doc = orchestrator.open_visual_script(path="scripts/dragon_ai.zvs")

    assert doc is not None
    assert doc.doc_type == DocumentType.VISUAL_SCRIPT

    DocumentManager._instance = None
