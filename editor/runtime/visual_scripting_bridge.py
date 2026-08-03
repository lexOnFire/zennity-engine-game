"""VisualScriptingBridge — Sprint 4b.

Conecta o VisualScriptingEditorDock ao Editor Framework 2.0:
  - EventBus (domínio Graph.*)
  - DocumentManager (abre/fecha documentos .zvs)
  - ToolRegistry (registra ferramenta com dock + atalhos)
  - SelectionService (nó selecionado no grafo → Inspector mostra propriedades do nó)

Uso:
    bridge = VisualScriptingBridge(editor_context)
    bridge.attach_dock(visual_scripting_dock)
    bridge.attach_reactive_bridge(reactive_editor_bridge)  # opcional
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class VisualLogicBridge:
    """Single bridge owner for the Visual Logic hub and all graph modes."""

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._dock: Any = None
        self._current_document: Any = None
        self._reactive_bridge: Any = None
        self._mode_bridges: dict[str, Any] = {}

        # Registra a ferramenta no ToolRegistry
        self._register_tool()

        # Subscreve nos Graph Events para propagar ao Inspector
        self._subscribe_graph_events()

    def attach_dock(self, dock: Any) -> None:
        """Conecta o VisualScriptingEditorDock."""
        self._dock = dock
        self._connect_dock_signals()
        if self._tool_def is not None:
            self._tool_def.dock = dock

    def attach_reactive_bridge(self, reactive_bridge: Any) -> None:
        self._reactive_bridge = reactive_bridge

    def mode_bridge(self, tool_id: str) -> Any:
        """Return the typed adapter owned by this bridge for a hub tab."""
        key = str(tool_id)
        if key in self._mode_bridges:
            return self._mode_bridges[key]
        from editor.runtime.graph_editor_bridge import GraphEditorBridge
        from editor.workspace.document_framework import DocumentType
        configs = {
            "behavior_tree": (DocumentType.BEHAVIOR_TREE, "bt"),
            "dialogue": (DocumentType.DIALOGUE, "dlg"),
            "material_graph": (DocumentType.MATERIAL, "mat"),
        }
        document_type, prefix = configs[key]
        bridge = GraphEditorBridge(self._ctx, key, document_type, prefix)
        self._mode_bridges[key] = bridge
        return bridge

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            tool = ToolDefinition(
                id="visual_scripting.editor",
                label="Editor de Lógica Visual",
                dock=None,
                shortcuts=["Ctrl+Shift+L"],
                commands=["graph.add_node", "graph.delete_node",
                          "graph.add_edge", "graph.delete_edge",
                          "graph.execute", "graph.reset"],
                menu="Janela",
                icon="graph",
                category="Editor",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception:
            self._tool_def = None

    # ── Document Management ───────────────────────────────────────────────────

    def open_script_document(self, path: str | Path | None = None, data: Any = None) -> Any:
        """Abre um arquivo .zvs como documento no DocumentManager."""
        try:
            from editor.workspace.document_framework import DocumentManager, DocumentType
            doc = DocumentManager.instance().open(
                DocumentType.VISUAL_SCRIPT,
                path=Path(path) if path else None,
                data=data,
            )
            self._current_document = doc

            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_SELECTED
            EventBus.emit(EVENT_GRAPH_NODE_SELECTED, node=None, document=doc)

            return doc
        except Exception as exc:
            print(f"[VisualScriptingBridge] open_script_document: {exc}")
            return None

    def close_script_document(self) -> None:
        if self._current_document is None:
            return
        try:
            from editor.workspace.document_framework import DocumentManager
            DocumentManager.instance().close(self._current_document)
        except Exception:
            pass
        self._current_document = None

    # ── Dock Signal Connections ───────────────────────────────────────────────

    def _connect_dock_signals(self) -> None:
        """Conecta sinais do GenericGraphEditorWidget ao EventBus."""
        if self._dock is None:
            return
        # O GenericGraphEditorWidget expõe graph_editor interno
        graph_editor = getattr(self._dock, "graph_editor", None)
        if graph_editor is None:
            return
        # Conecta seleção de nó (se o widget tiver esse sinal)
        self._try_connect(graph_editor, "node_selected", self._on_node_selected)
        self._try_connect(graph_editor, "node_added", self._on_node_added)
        self._try_connect(graph_editor, "node_deleted", self._on_node_deleted)
        self._try_connect(graph_editor, "edge_added", self._on_edge_added)

    def _try_connect(self, obj: Any, signal_name: str, handler: Any) -> None:
        try:
            signal = getattr(obj, signal_name, None)
            if signal is not None:
                signal.connect(handler)
        except Exception:
            pass

    # ── Graph Event Handlers → EventBus ──────────────────────────────────────

    def _on_node_selected(self, node: Any) -> None:
        """Nó selecionado no grafo → emite Selection.changed + Graph.node_selected."""
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_SELECTED
            EventBus.emit(EVENT_GRAPH_NODE_SELECTED, node=node,
                          document=self._current_document)

            # Propaga seleção do nó para o Inspector via SelectionService
            if node is not None:
                self._ctx.selection.select_item(
                    node,
                    type="node",
                    context="visual_scripting",
                    id=str(getattr(node, "node_id", id(node))),
                )
        except Exception:
            pass

    def _on_node_added(self, node: Any) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_ADDED
            EventBus.emit(EVENT_GRAPH_NODE_ADDED, node=node,
                          document=self._current_document)
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass

    def _on_node_deleted(self, node: Any) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_DELETED
            EventBus.emit(EVENT_GRAPH_NODE_DELETED, node=node,
                          document=self._current_document)
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass

    def _on_edge_added(self, edge: Any) -> None:
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_EDGE_ADDED
            EventBus.emit(EVENT_GRAPH_EDGE_ADDED, edge=edge,
                          document=self._current_document)
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass

    # ── Subscribe Graph Events ────────────────────────────────────────────────

    def _subscribe_graph_events(self) -> None:
        """Subscreve nos Graph Events para reações cruzadas."""
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_SELECTED
            EventBus.subscribe(EVENT_GRAPH_NODE_SELECTED, self._on_graph_node_selected_event)
        except Exception:
            pass

    def _on_graph_node_selected_event(self, **kwargs: Any) -> None:
        """Reage a seleção de nó de outros editores de grafo (BehaviorTree, Material)."""
        pass  # extensão futura: sincronizar estado com outros grafos abertos

    # ── Node API ──────────────────────────────────────────────────────────────

    def add_node(self, node_type: str, position: tuple = (0, 0)) -> None:
        """API pública para adicionar nó ao grafo ativo."""
        try:
            from editor.core.event_bus import EventBus, EVENT_GRAPH_NODE_ADDED
            EventBus.emit(EVENT_GRAPH_NODE_ADDED, node_type=node_type,
                          position=position, document=self._current_document)
            if self._current_document:
                self._current_document.mark_modified()
        except Exception:
            pass

    def execute_graph(self) -> None:
        """Dispara execução do grafo ativo."""
        if self._dock is None:
            return
        try:
            graph_editor = getattr(self._dock, "graph_editor", None)
            if graph_editor and hasattr(graph_editor, "execute"):
                graph_editor.execute()
        except Exception:
            pass


# Public compatibility name for extensions built against the pre-consolidation API.
VisualScriptingBridge = VisualLogicBridge

__all__ = ["VisualLogicBridge", "VisualScriptingBridge"]
