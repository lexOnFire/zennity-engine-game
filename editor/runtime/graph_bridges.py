"""Fábricas dos bridges de grafo especializados (Sprint 4c).

Cada bridge configura o GraphEditorBridge com seu DocumentType,
tool_id e prefixo de evento correto.

Uso direto:
    from editor.runtime.graph_bridges import (
        BehaviorTreeBridge, DialogueBridge, MaterialGraphBridge
    )
    bt      = BehaviorTreeBridge(editor_context)
    dlg     = DialogueBridge(editor_context)
    mat     = MaterialGraphBridge(editor_context)

Ou via Orchestrator (recomendado):
    orchestrator.setup(
        behavior_tree_dock=dock_bt,
        dialogue_dock=dock_dlg,
        material_dock=dock_mat,
    )
"""
from __future__ import annotations

from typing import Any

from editor.runtime.graph_editor_bridge import GraphEditorBridge


def BehaviorTreeBridge(editor_context: Any) -> GraphEditorBridge:
    """Bridge para o BehaviorTreeEditorDock."""
    from editor.workspace.document_framework import DocumentType
    return GraphEditorBridge(
        editor_context=editor_context,
        tool_id="behavior_tree",
        document_type=DocumentType.BEHAVIOR_TREE,
        event_prefix="bt",
    )


def DialogueBridge(editor_context: Any) -> GraphEditorBridge:
    """Bridge para o DialogueGraphEditorDock."""
    from editor.workspace.document_framework import DocumentType
    return GraphEditorBridge(
        editor_context=editor_context,
        tool_id="dialogue",
        document_type=DocumentType.DIALOGUE,
        event_prefix="dlg",
    )


def MaterialGraphBridge(editor_context: Any) -> GraphEditorBridge:
    """Bridge para o MaterialGraphEditorDock."""
    from editor.workspace.document_framework import DocumentType
    return GraphEditorBridge(
        editor_context=editor_context,
        tool_id="material_graph",
        document_type=DocumentType.MATERIAL,
        event_prefix="mat",
    )
