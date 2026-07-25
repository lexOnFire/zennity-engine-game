"""GraphEditorBridge — Bridge genérico para editores baseados no GenericGraphEditorWidget.

Sprint 4c: serve para BehaviorTree, Dialogue e Material Graph —
todos são especializações do mesmo widget de grafo.

Cada bridge instancia com um DocumentType e um prefixo de ferramenta:

    BehaviorTreeBridge  = GraphEditorBridge(ctx, "behavior_tree",  DocumentType.BEHAVIOR_TREE,  "Graph.bt.*")
    DialogueBridge      = GraphEditorBridge(ctx, "dialogue",       DocumentType.DIALOGUE,        "Graph.dlg.*")
    MaterialGraphBridge = GraphEditorBridge(ctx, "material_graph", DocumentType.MATERIAL,        "Graph.mat.*")

Integra com:
  - EventBus  (Graph.* Events com sub-prefixo por tipo de grafo)
  - DocumentManager (DocumentType correto por bridge)
  - ToolRegistry (tool_id, label, shortcuts, commands únicos)
  - SelectionService (nó selecionado → Inspector via type="node", context=tool_id)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


_TOOL_CONFIGS = {
    "behavior_tree": {
        "label": "Behavior Tree Editor",
        "shortcuts": ["Ctrl+Shift+B"],
        "commands": [
            "bt.add_node", "bt.delete_node", "bt.add_edge",
            "bt.validate", "bt.simulate",
        ],
        "icon": "brain",
        "menu": "Ferramentas",
    },
    "dialogue": {
        "label": "Dialogue Graph Editor",
        "shortcuts": ["Ctrl+Shift+D"],
        "commands": [
            "dlg.add_node", "dlg.delete_node", "dlg.add_edge",
            "dlg.preview", "dlg.export",
        ],
        "icon": "dialogue",
        "menu": "Ferramentas",
    },
    "material_graph": {
        "label": "Material Graph Editor",
        "shortcuts": ["Ctrl+Shift+M"],
        "commands": [
            "mat.add_node", "mat.delete_node", "mat.add_edge",
            "mat.compile", "mat.preview",
        ],
        "icon": "material",
        "menu": "Ferramentas",
    },
}


class GraphEditorBridge:
    """Bridge genérico para editores de grafo baseados no GenericGraphEditorWidget.

    Configurado com tool_id, DocumentType e prefixo de evento.
    """

    def __init__(
        self,
        editor_context: Any,
        tool_id: str,
        document_type: Any,
        event_prefix: str,
    ) -> None:
        self._ctx = editor_context
        self._tool_id = tool_id
        self._doc_type = document_type
        self._event_prefix = event_prefix
        self._dock: Any = None
        self._current_document: Any = None
        self._tool_def: Any = None

        self._register_tool()
        self._subscribe_events()

    def attach_dock(self, dock: Any) -> None:
        """Conecta o dock de grafo especializado."""
        self._dock = dock
        if self._tool_def is not None:
            self._tool_def.dock = dock
        self._connect_dock_signals()

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            cfg = _TOOL_CONFIGS.get(self._tool_id, {})
            tool = ToolDefinition(
                id=self._tool_id,
                label=cfg.get("label", self._tool_id),
                dock=None,
                shortcuts=cfg.get("shortcuts", []),
                commands=cfg.get("commands", []),
                menu=cfg.get("menu", "Ferramentas"),
                icon=cfg.get("icon", ""),
                category="Editor",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception as exc:
            print(f"[GraphEditorBridge:{self._tool_id}] _register_tool: {exc}")

    # ── Document Management ───────────────────────────────────────────────────

    def open_document(self, path: str | Path | None = None, data: Any = None) -> Any:
        """Abre um documento do tipo correto no DocumentManager."""
        try:
            from editor.workspace.document_framework import DocumentManager
            doc = DocumentManager.instance().open(
                self._doc_type,
                path=Path(path) if path else None,
                data=data,
            )
            self._current_document = doc
            self._emit("opened", document=doc)
            return doc
        except Exception as exc:
            print(f"[GraphEditorBridge:{self._tool_id}] open_document: {exc}")
            return None

    def close_document(self) -> None:
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
        if self._dock is None:
            return
        graph_editor = getattr(self._dock, "graph_editor", None)
        if graph_editor is None:
            return
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

    # ── Graph Handlers → EventBus ─────────────────────────────────────────────

    def _on_node_selected(self, node: Any) -> None:
        self._emit("node_selected", node=node)
        if node is not None:
            self._ctx.selection.select_item(
                node,
                type="node",
                context=self._tool_id,
                id=str(getattr(node, "node_id", id(node))),
            )

    def _on_node_added(self, node: Any) -> None:
        self._emit("node_added", node=node)
        self._mark_modified()

    def _on_node_deleted(self, node: Any) -> None:
        self._emit("node_deleted", node=node)
        self._mark_modified()

    def _on_edge_added(self, edge: Any) -> None:
        self._emit("edge_added", edge=edge)
        self._mark_modified()

    # ── Event Subscriptions ───────────────────────────────────────────────────

    def _subscribe_events(self) -> None:
        """Subscreve no EventBus para reagir a eventos externos."""
        pass  # extensível por subclasses ou configuração

    # ── Node API ──────────────────────────────────────────────────────────────

    def add_node(self, node_type: str, position: tuple = (0, 0)) -> None:
        """API pública para adicionar nó ao grafo ativo."""
        self._emit("node_added", node_type=node_type, position=position)
        self._mark_modified()

    def add_edge(self, from_id: str, to_id: str) -> None:
        """API pública para adicionar aresta entre dois nós."""
        self._emit("edge_added", from_id=from_id, to_id=to_id)
        self._mark_modified()

    def execute(self) -> None:
        """Executa/valida o grafo ativo."""
        self._emit("executed")
        if self._dock:
            graph_editor = getattr(self._dock, "graph_editor", None)
            if graph_editor and hasattr(graph_editor, "execute"):
                graph_editor.execute()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _emit(self, sub_event: str, **kwargs: Any) -> None:
        """Emite evento no domínio Graph.* com prefixo do tool_id."""
        try:
            from editor.core.event_bus import EventBus
            event_name = f"Graph.{self._event_prefix}.{sub_event}"
            EventBus.emit(event_name, tool_id=self._tool_id,
                          document=self._current_document, **kwargs)
        except Exception:
            pass

    def _mark_modified(self) -> None:
        if self._current_document:
            self._current_document.mark_modified()

    @property
    def tool_id(self) -> str:
        return self._tool_id

    @property
    def current_document(self) -> Any:
        return self._current_document
