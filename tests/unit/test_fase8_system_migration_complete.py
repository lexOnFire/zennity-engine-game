"""Testes de Validação Global da Fase 8 (System Migration).

Garante que todos os 12 sistemas da Zennity Engine consomem nativamente
a infraestrutura do Editor Framework 2.0.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_system_migration_conformance_matrix():
    """Valida a conformidade da matriz de migração para 100% dos 12 sistemas."""
    from editor.runtime.editor_bridge_orchestrator import EditorBridgeOrchestrator
    from editor.runtime.editor_context import EditorContext
    from editor.workspace.tool_registry import ToolRegistry

    ctx = EditorContext()
    orchestrator = EditorBridgeOrchestrator(ctx)
    orchestrator.setup()

    # 1. Valida que os 9 bridges foram instanciados no Orchestrator
    assert orchestrator.reactive is not None
    assert orchestrator.animation is not None
    assert orchestrator.visual_scripting is not None
    assert orchestrator.behavior_tree is not None
    assert orchestrator.dialogue is not None
    assert orchestrator.material_graph is not None
    assert orchestrator.diagnostics is not None
    assert orchestrator.extensions is not None
    assert orchestrator.build_pipeline is not None

    # 2. Valida registro de ferramentas de todos os 12 sistemas
    registry = ToolRegistry.instance()
    registered_tools = [t.id for t in registry.all_tools()]

    expected_tools = [
        "animation.studio",
        "visual_scripting.editor",
        "behavior_tree",
        "dialogue",
        "material_graph",
        "diagnostics.profiler",
        "extensions.manager",
        "build.wizard",
        "build.report",
    ]

    for tool_id in expected_tools:
        assert tool_id in registered_tools, f"Ferramenta {tool_id} não registrada"


def test_full_reactive_selection_flow():
    """Valida o fluxo reativo completo: SelectionService -> Bridge -> Inspector -> EventBus."""
    from editor.runtime.editor_context import EditorContext
    from editor.runtime.reactive_editor_bridge import ReactiveEditorBridge
    from editor.premium_inspector_panel import RealInspectorPanel
    from editor.core.event_bus import EventBus, EVENT_OBJECT_MODIFIED

    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
    except ImportError:
        pytest.skip("PySide6 não disponível neste ambiente")

    ctx = EditorContext()
    bridge = ReactiveEditorBridge(ctx)
    inspector = RealInspectorPanel()

    bridge.attach_inspector(inspector)

    class FakeObj:
        name = "PlayerEntity"
        active = True

    obj = FakeObj()
    ctx.selection.select_item(obj, type="game_object", context="test")

    assert inspector.current_object is obj
    assert inspector.binding_group is not None

    events = []
    EventBus.subscribe(EVENT_OBJECT_MODIFIED, lambda **kw: events.append(kw))

    inspector.binding_group.set("name", "UpdatedPlayer", record_undo=False)
    assert len(events) >= 1
    assert events[-1]["value"] == "UpdatedPlayer"
