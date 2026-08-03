"""Testes unitários do Sprint 4c — Behavior Tree, Dialogue e Material Graph integrados.

Valida:
  - GraphEditorBridge genérico (DocumentManager, ToolRegistry, EventBus, SelectionService)
  - BehaviorTreeBridge, DialogueBridge, MaterialGraphBridge via fábricas
  - EditorBridgeOrchestrator expandido com os 3 novos bridges
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fakes
# ─────────────────────────────────────────────────────────────────────────────

class FakeEditorContext:
    def __init__(self):
        from editor.runtime.selection_manager import SelectionService
        self.selection = SelectionService()


class FakeGraphDock:
    def __init__(self, category="Generic"):
        self.graph_editor = FakeGraphWidget(category)


class FakeGraphWidget:
    def __init__(self, category="Generic"):
        self.category = category
        self._node_selected_cbs = []
        self._node_added_cbs = []

    def simulate_node_selected(self, node):
        for cb in self._node_selected_cbs:
            cb(node)

    def simulate_node_added(self, node):
        for cb in self._node_added_cbs:
            cb(node)


class FakeNode:
    def __init__(self, node_id="n1", label="Node"):
        self.node_id = node_id
        self.label = label


class FakeInspector:
    def __init__(self):
        self.last_loaded = "NOT_SET"

    def load_object(self, obj):
        self.last_loaded = obj


class FakeHierarchy:
    def __init__(self):
        self.last_selected = "NOT_SET"

    def select_object_in_tree(self, obj):
        self.last_selected = obj


class FakeViewport:
    def __init__(self):
        self.last_selected = "NOT_SET"

    def select_object(self, obj):
        self.last_selected = obj


def _fresh_doc_manager():
    from editor.workspace.document_framework import DocumentManager
    mgr = DocumentManager()
    DocumentManager._instance = mgr
    return mgr


def _cleanup_doc_manager():
    from editor.workspace.document_framework import DocumentManager
    DocumentManager._instance = None


# ─────────────────────────────────────────────────────────────────────────────
# GraphEditorBridge — testes genéricos
# ─────────────────────────────────────────────────────────────────────────────

def test_graph_bridge_registers_behavior_tree_tool():
    """BehaviorTreeBridge registra 'behavior_tree' no ToolRegistry."""
    from editor.runtime.graph_bridges import BehaviorTreeBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = BehaviorTreeBridge(ctx)

    tool = ToolRegistry.instance().get("behavior_tree")
    assert tool is not None
    assert tool.id == "behavior_tree"
    assert "bt.add_node" in tool.commands
    assert "Ctrl+Shift+B" in tool.shortcuts
    assert tool.menu == "Editor de Lógica Visual"


def test_graph_bridge_registers_dialogue_tool():
    """DialogueBridge registra 'dialogue' no ToolRegistry."""
    from editor.runtime.graph_bridges import DialogueBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = DialogueBridge(ctx)

    tool = ToolRegistry.instance().get("dialogue")
    assert tool is not None
    assert "dlg.add_node" in tool.commands
    assert "Ctrl+Shift+D" in tool.shortcuts


def test_graph_bridge_registers_material_tool():
    """MaterialGraphBridge registra 'material_graph' no ToolRegistry."""
    from editor.runtime.graph_bridges import MaterialGraphBridge
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    bridge = MaterialGraphBridge(ctx)

    tool = ToolRegistry.instance().get("material_graph")
    assert tool is not None
    assert "mat.add_node" in tool.commands
    assert "Ctrl+Shift+M" in tool.shortcuts


def test_behavior_tree_bridge_open_document():
    """BehaviorTreeBridge abre documento BEHAVIOR_TREE no DocumentManager."""
    from editor.runtime.graph_bridges import BehaviorTreeBridge
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = BehaviorTreeBridge(ctx)

    doc = bridge.open_document(path="ai/enemy_patrol.zbtree")

    assert doc is not None
    assert doc.doc_type == DocumentType.BEHAVIOR_TREE
    assert "enemy_patrol" in str(doc.path)
    _cleanup_doc_manager()


def test_dialogue_bridge_open_document():
    """DialogueBridge abre documento DIALOGUE no DocumentManager."""
    from editor.runtime.graph_bridges import DialogueBridge
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = DialogueBridge(ctx)

    doc = bridge.open_document(path="dialogue/npc_merchant.zdlg")

    assert doc is not None
    assert doc.doc_type == DocumentType.DIALOGUE
    assert "npc_merchant" in str(doc.path)
    _cleanup_doc_manager()


def test_material_graph_bridge_open_document():
    """MaterialGraphBridge abre documento MATERIAL no DocumentManager."""
    from editor.runtime.graph_bridges import MaterialGraphBridge
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = MaterialGraphBridge(ctx)

    doc = bridge.open_document(path="materials/lava.zmat")

    assert doc is not None
    assert doc.doc_type == DocumentType.MATERIAL
    assert "lava" in str(doc.path)
    _cleanup_doc_manager()


def test_behavior_tree_bridge_add_node_emits_event():
    """BehaviorTreeBridge.add_node() emite Graph.bt.node_added via EventBus."""
    from editor.runtime.graph_bridges import BehaviorTreeBridge
    from editor.core.event_bus import EventBus

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = BehaviorTreeBridge(ctx)
    bridge.open_document(path="ai/boss.zbtree")

    received = []
    EventBus.subscribe("Graph.bt.node_added", lambda **kw: received.append(kw))

    bridge.add_node("SequenceNode", position=(50, 100))

    assert any(r.get("node_type") == "SequenceNode" for r in received)
    assert bridge.current_document.is_modified
    _cleanup_doc_manager()


def test_dialogue_bridge_add_node_emits_event():
    """DialogueBridge.add_node() emite Graph.dlg.node_added via EventBus."""
    from editor.runtime.graph_bridges import DialogueBridge
    from editor.core.event_bus import EventBus

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = DialogueBridge(ctx)
    bridge.open_document(path="dialogue/intro.zdlg")

    received = []
    EventBus.subscribe("Graph.dlg.node_added", lambda **kw: received.append(kw))

    bridge.add_node("SpeechNode", position=(0, 0))

    assert any(r.get("node_type") == "SpeechNode" for r in received)
    _cleanup_doc_manager()


def test_material_bridge_add_node_emits_event():
    """MaterialGraphBridge.add_node() emite Graph.mat.node_added via EventBus."""
    from editor.runtime.graph_bridges import MaterialGraphBridge
    from editor.core.event_bus import EventBus

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = MaterialGraphBridge(ctx)
    bridge.open_document(path="materials/water.zmat")

    received = []
    EventBus.subscribe("Graph.mat.node_added", lambda **kw: received.append(kw))

    bridge.add_node("TextureNode", position=(100, 50))

    assert any(r.get("node_type") == "TextureNode" for r in received)
    _cleanup_doc_manager()


def test_behavior_tree_node_selection_propagates_to_inspector():
    """Nó do BehaviorTree selecionado propaga para Inspector via SelectionService."""
    from editor.runtime.graph_bridges import BehaviorTreeBridge
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge

    ctx = FakeEditorContext()
    reactive = ReactiveEditorBridge(ctx)
    inspector = FakeInspector()
    reactive.attach_inspector(inspector)

    bridge = BehaviorTreeBridge(ctx)

    node = FakeNode("bt_seq_1", "Sequence")
    ctx.selection.select_item(node, type="node", context="behavior_tree", id="bt_seq_1")

    assert inspector.last_loaded is node


def test_material_node_selection_has_correct_context():
    """Nó do Material Graph selecionado usa context='material_graph' no SelectionItem."""
    from editor.runtime.graph_bridges import MaterialGraphBridge

    ctx = FakeEditorContext()
    bridge = MaterialGraphBridge(ctx)

    node = FakeNode("tex_001", "Texture")
    # Simula seleção como o bridge faria ao receber node_selected do dock
    bridge._on_node_selected(node)

    item = ctx.selection.current_item
    assert item is not None
    assert item.type == "node"
    assert item.context == "material_graph"
    assert item.payload is node


def test_graph_bridge_add_edge_marks_document_modified():
    """add_edge() marca o documento como modificado."""
    from editor.runtime.graph_bridges import DialogueBridge

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    bridge = DialogueBridge(ctx)
    bridge.open_document(path="dlg/test.zdlg")

    assert not bridge.current_document.is_modified
    bridge.add_edge("node_a", "node_b")
    assert bridge.current_document.is_modified
    _cleanup_doc_manager()


# ─────────────────────────────────────────────────────────────────────────────
# EditorBridgeOrchestrator expandido — Sprint 4c
# ─────────────────────────────────────────────────────────────────────────────

def test_orchestrator_creates_all_six_bridges():
    """EditorBridgeOrchestrator cria os 6 bridges (incluindo BT, Dialogue, Material)."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    assert orchestrator.reactive is not None
    assert orchestrator.animation is not None
    assert orchestrator.visual_scripting is not None
    assert orchestrator.behavior_tree is not None
    assert orchestrator.dialogue is not None
    assert orchestrator.material_graph is not None


def test_orchestrator_open_behavior_tree_returns_document():
    """Orchestrator.open_behavior_tree() retorna EditorDocument do tipo BEHAVIOR_TREE."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    doc = orchestrator.open_behavior_tree(path="ai/patrol.zbtree")

    assert doc is not None
    assert doc.doc_type == DocumentType.BEHAVIOR_TREE
    _cleanup_doc_manager()


def test_orchestrator_open_dialogue_returns_document():
    """Orchestrator.open_dialogue() retorna EditorDocument do tipo DIALOGUE."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    doc = orchestrator.open_dialogue(path="dlg/quest_intro.zdlg")

    assert doc is not None
    assert doc.doc_type == DocumentType.DIALOGUE
    _cleanup_doc_manager()


def test_orchestrator_open_material_returns_document():
    """Orchestrator.open_material() retorna EditorDocument do tipo MATERIAL."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.document_framework import DocumentType

    _fresh_doc_manager()
    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    doc = orchestrator.open_material(path="mats/fire.zmat")

    assert doc is not None
    assert doc.doc_type == DocumentType.MATERIAL
    _cleanup_doc_manager()


def test_orchestrator_all_tools_registered():
    """Todos os 5 editores de grafo estão registrados no ToolRegistry após setup."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    registry = ToolRegistry.instance()
    expected = [
        "animation.studio",
        "visual_scripting.editor",
        "behavior_tree",
        "dialogue",
        "material_graph",
    ]
    for tool_id in expected:
        assert registry.get(tool_id) is not None, f"Ferramenta '{tool_id}' não registrada"


def test_orchestrator_activate_shortcuts_all_tools():
    """Cada ferramenta tem atalho de teclado configurado."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.workspace.tool_registry import ToolRegistry

    ctx = FakeEditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    registry = ToolRegistry.instance()
    shortcuts_map = {
        "animation.studio": "Ctrl+Shift+A",
        "visual_scripting.editor": "Ctrl+Shift+L",
        "behavior_tree": "Ctrl+Shift+B",
        "dialogue": "Ctrl+Shift+D",
        "material_graph": "Ctrl+Shift+M",
    }
    for tool_id, expected_shortcut in shortcuts_map.items():
        tool = registry.get(tool_id)
        assert tool is not None
        assert expected_shortcut in tool.shortcuts, \
            f"Atalho '{expected_shortcut}' não encontrado em '{tool_id}'"
