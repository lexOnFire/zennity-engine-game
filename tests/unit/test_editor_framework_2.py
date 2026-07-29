"""Testes unitários do Editor Framework 2.0.

Cobre Sprint 1 (Context/Events/Selection), Sprint 2 (Actions/Properties)
e Sprint 3 (Workspace/Tools/Documents).
"""
from __future__ import annotations

import sys
import os

# Garante que a raiz do projeto está no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 1 — EditorApplication, EditorContext, SceneContext
# ─────────────────────────────────────────────────────────────────────────────

def test_editor_application_context_hierarchy():
    """Valida EditorApplication → EditorContext → SceneContext sem God Object."""
    from editor.core.editor_application import EditorApplication
    from editor.runtime.editor_context import EditorContext
    from editor.runtime.scene_context import SceneContext

    app = EditorApplication(app_name="TestApp")
    ctx = EditorContext()
    scene_ctx = ctx.open_scene(scene=None)

    assert isinstance(app, EditorApplication)
    assert isinstance(ctx, EditorContext)
    assert isinstance(scene_ctx, SceneContext)

    # EditorContext não conhece plugins nem tema (esses estão no EditorApplication)
    assert not hasattr(ctx, "_plugins")
    assert not hasattr(ctx, "_theme")

    # SceneContext não conhece selection nem commands (esses estão no EditorContext)
    assert not hasattr(scene_ctx, "selection")
    assert not hasattr(scene_ctx, "commands")

    # SceneContext pode tirar snapshot para persistência de workspace
    snap = scene_ctx.snapshot()
    assert "camera_zoom" in snap
    assert "active_tool" in snap
    assert "grid_size" in snap


def test_scene_context_snapshot_and_restore():
    """Valida que SceneContext serializa e restaura estado completo."""
    from editor.runtime.scene_context import SceneContext

    ctx = SceneContext()
    ctx.set_camera(100.0, 200.0, zoom=2.5, mode="2D")
    ctx.set_active_tool("move")
    ctx.grid_size = 64

    snap = ctx.snapshot()
    assert snap["camera_position"] == [100.0, 200.0]
    assert snap["camera_zoom"] == 2.5
    assert snap["active_tool"] == "move"
    assert snap["grid_size"] == 64

    ctx2 = SceneContext()
    ctx2.restore(snap)
    assert ctx2.camera_zoom == 2.5
    assert ctx2.active_tool == "move"
    assert ctx2.grid_size == 64


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 1 — SelectionItem genérico
# ─────────────────────────────────────────────────────────────────────────────

def test_selection_item_generic_dispatch():
    """Valida SelectionItem genérico que não conhece tipos específicos."""
    from editor.runtime.selection_manager import SelectionItem, SelectionService

    svc = SelectionService()
    received: list = []
    svc.subscribe(received.append)

    # Seleciona qualquer tipo via interface genérica
    class FakeNode:
        name = "StartNode"

    node = FakeNode()
    svc.select_item(node, type="node", context="behavior_tree", id="node_start")

    assert len(received) == 1
    assert received[0] is node
    assert svc.current_item is not None
    assert svc.current_item.type == "node"
    assert svc.current_item.context == "behavior_tree"
    assert svc.current_item.id == "node_start"
    assert svc.current_item.payload is node


def test_selection_service_clear_resets_item():
    """Valida que clear_selection zera o SelectionItem atual."""
    from editor.runtime.selection_manager import SelectionService

    svc = SelectionService()
    svc.select_item("asset.png", type="asset", context="asset_browser")
    assert svc.current_item is not None

    svc.clear_selection()
    assert svc.current_item is None
    assert svc.selected is None


def test_selection_service_notify_multiple_subscribers():
    """Valida que múltiplos sistemas recebem a mudança de seleção."""
    from editor.runtime.selection_manager import SelectionService

    svc = SelectionService()
    results_a: list = []
    results_b: list = []
    results_c: list = []

    svc.subscribe(results_a.append)
    svc.subscribe(results_b.append)
    svc.subscribe(results_c.append)

    svc.select_item("obj_x", type="game_object", context="hierarchy")

    assert len(results_a) == 1
    assert len(results_b) == 1
    assert len(results_c) == 1


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 1 — Event Domains
# ─────────────────────────────────────────────────────────────────────────────

def test_event_domain_constants_exist():
    """Valida que todos os Event Domains estão definidos no event_bus."""
    from editor.core.event_bus import (
        EVENT_SCENE_OPENED, EVENT_SCENE_CLOSED, EVENT_OBJECT_CREATED,
        EVENT_SELECTION_CHANGED, EVENT_SELECTION_CLEARED,
        EVENT_WORKSPACE_CHANGED, EVENT_PANEL_OPENED,
        EVENT_ANIMATION_KEYFRAME, EVENT_ANIMATION_PLAYBACK,
        EVENT_GRAPH_NODE_SELECTED, EVENT_GRAPH_NODE_ADDED,
        EVENT_BUILD_STARTED, EVENT_BUILD_COMPLETED,
        EVENT_PLAY_STATE_CHANGED, EVENT_RUNTIME_LOG,
    )
    assert EVENT_SCENE_OPENED.startswith("Scene.")
    assert EVENT_SELECTION_CHANGED.startswith("Selection.")
    assert EVENT_WORKSPACE_CHANGED.startswith("Workspace.")
    assert EVENT_ANIMATION_KEYFRAME.startswith("Animation.")
    assert EVENT_GRAPH_NODE_SELECTED.startswith("Graph.")
    assert EVENT_BUILD_STARTED.startswith("Build.")
    assert EVENT_PLAY_STATE_CHANGED.startswith("Runtime.")


def test_event_bus_emit_and_subscribe():
    """Valida emissão e recepção de eventos com domínio."""
    from editor.core.event_bus import EventBus, EVENT_SELECTION_CHANGED

    received = []

    def handler(**kwargs):
        received.append(kwargs)

    EventBus.subscribe(EVENT_SELECTION_CHANGED, handler)
    EventBus.emit(EVENT_SELECTION_CHANGED, selection="player_obj", selection_type="game_object")
    assert len(received) >= 1
    assert received[0]["selection"] == "player_obj"


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 2 — Action System
# ─────────────────────────────────────────────────────────────────────────────

def test_action_system_unified_registration():
    """Valida mesma ação reutilizada em múltiplos contextos."""
    from editor.core.action_system import EditorAction, ActionRegistry

    called: list = []
    action = EditorAction(
        id="scene.new",
        label="Nova Cena",
        shortcut="Ctrl+N",
        handler=lambda: called.append("new_scene"),
        category="Arquivo",
        tags=["cena", "novo"],
    )

    registry = ActionRegistry()
    registry.register(action)

    assert registry.get("scene.new") is action

    # A mesma ação pode ser disparada via trigger
    registry.trigger("scene.new")
    assert len(called) == 1

    # E pesquisada por texto ou tag
    results = registry.search("cena")
    assert any(a.id == "scene.new" for a in results)

    arquivo_actions = registry.by_category("Arquivo")
    assert any(a.id == "scene.new" for a in arquivo_actions)


def test_action_disabled_does_not_call_handler():
    """Valida que ação desabilitada não dispara o handler."""
    from editor.core.action_system import EditorAction

    called: list = []
    action = EditorAction(
        id="test.disabled",
        label="Ação Desabilitada",
        handler=lambda: called.append("called"),
        enabled=False,
    )
    action.trigger()
    assert len(called) == 0


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 2 — Property Binding
# ─────────────────────────────────────────────────────────────────────────────

def test_property_binding_set_and_notify():
    """Valida que PropertyBinding notifica callback ao alterar valor."""
    from editor.core.property_binding import PropertyBinding

    class Obj:
        speed = 100.0

    obj = Obj()
    notified: list = []
    binding = PropertyBinding(obj, "speed", label="Velocidade", on_changed=notified.append)

    binding.set(200.0, record_undo=False)
    assert obj.speed == 200.0
    assert len(notified) == 1
    assert notified[0] == 200.0


def test_property_binding_group_serialize_and_deserialize():
    """Valida PropertyBindingGroup serializa e restaura múltiplas propriedades."""
    from editor.core.property_binding import PropertyBindingGroup

    class Player:
        speed = 100.0
        health = 80
        name = "Hero"

    obj = Player()
    group = PropertyBindingGroup(obj)
    group.bind("speed", label="Velocidade")
    group.bind("health", label="Vida")
    group.bind("name", label="Nome")

    group.set("speed", 250.0, record_undo=False)
    group.set("health", 50, record_undo=False)

    data = group.serialize_all()
    assert data["speed"] == 250.0
    assert data["health"] == 50
    assert data["name"] == "Hero"

    obj2 = Player()
    group2 = PropertyBindingGroup(obj2)
    group2.bind("speed")
    group2.bind("health")
    group2.bind("name")
    group2.deserialize_all(data)

    assert obj2.speed == 250.0
    assert obj2.health == 50
    assert obj2.name == "Hero"


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 3 — Tool Registry
# ─────────────────────────────────────────────────────────────────────────────

def test_tool_definition_registry():
    """Valida registro de ferramentas com docks + atalhos."""
    from editor.workspace.tool_registry import ToolDefinition, ToolRegistry

    registry = ToolRegistry()

    anim_tool = ToolDefinition(
        id="animation.studio",
        label="Animation Studio",
        shortcuts=["Ctrl+Shift+A"],
        commands=["animation.play", "animation.stop"],
        menu="Janela",
        category="Editor",
    )
    registry.register(anim_tool)

    vs_tool = ToolDefinition(
        id="visual_scripting.editor",
        label="Editor de Lógica Visual",
        shortcuts=["Ctrl+Shift+L"],
        commands=["graph.add_node", "graph.delete_node"],
        menu="Janela",
        category="Editor",
    )
    registry.register(vs_tool)

    assert registry.get("animation.studio") is anim_tool
    assert registry.get("visual_scripting.editor") is vs_tool

    editor_tools = registry.by_category("Editor")
    assert len(editor_tools) >= 2

    all_tools = registry.all_tools()
    assert any(t.id == "animation.studio" for t in all_tools)


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 3 — Document Framework
# ─────────────────────────────────────────────────────────────────────────────

def test_document_framework_open_and_activate():
    """Valida abertura, ativação e rastreamento de documentos."""
    from editor.workspace.document_framework import DocumentManager, DocumentType

    mgr = DocumentManager()

    from pathlib import Path
    doc_scene = mgr.open(DocumentType.SCENE, path=Path("levels/level1.zscene"))
    doc_anim = mgr.open(DocumentType.ANIMATION, path=Path("anims/walk.zanim"))

    assert len(mgr.all_documents) == 2
    assert mgr.active is doc_anim  # último aberto é o ativo

    mgr.set_active(doc_scene)
    assert mgr.active is doc_scene

    doc_scene.mark_modified()
    assert doc_scene.is_modified
    assert "*" in doc_scene.display_title

    mgr.close(doc_scene)
    assert len(mgr.all_documents) == 1
    assert mgr.active is doc_anim


def test_document_type_from_extension():
    """Valida detecção automática de tipo de documento a partir da extensão."""
    from editor.workspace.document_framework import DocumentType

    assert DocumentType.from_extension("scene.zscene") == DocumentType.SCENE
    assert DocumentType.from_extension("mat.zmat") == DocumentType.MATERIAL
    assert DocumentType.from_extension("anim.zanim") == DocumentType.ANIMATION
    assert DocumentType.from_extension("script.zvs") == DocumentType.VISUAL_SCRIPT
    assert DocumentType.from_extension("ui.zui") == DocumentType.UI
    assert DocumentType.from_extension("unknown.xyz") == DocumentType.UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 3 — EditorApplication user workspaces
# ─────────────────────────────────────────────────────────────────────────────

def test_editor_application_user_workspaces():
    """Valida que EditorApplication persiste workspaces criados pelo usuário."""
    from editor.core.editor_application import EditorApplication

    app = EditorApplication(app_name="TestWorkspaceApp")

    layout = {
        "open_docks": ["hierarchy", "inspector", "animation_studio"],
        "camera_zoom": 1.5,
        "active_tool": "move",
        "grid_size": 32,
    }
    app.save_user_workspace("Meu Workspace de Animação", layout)
    assert "Meu Workspace de Animação" in app.list_user_workspaces()

    restored = app.load_user_workspace("Meu Workspace de Animação")
    assert restored["camera_zoom"] == 1.5
    assert "animation_studio" in restored["open_docks"]

    app.delete_user_workspace("Meu Workspace de Animação")
    assert "Meu Workspace de Animação" not in app.list_user_workspaces()
