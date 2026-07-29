"""UIBuilderBridge — Bridge do UI Builder para o Editor Framework 2.0 (Fase 8.4).

Conecta o UIBuilderDock ao Editor Framework 2.0:
  - SelectionService (trata componentes visuais de UI como SelectionItem genérico)
  - PropertyBinding & PropertyBindingGroup
  - EventBus (domínio UI.*)
  - ToolRegistry (registra 'ui.builder')
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


class UIBuilderBridge:
    """Integra o UIBuilderDock ao Editor Framework 2.0."""

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._dock: Any = None
        self._current_document: Any = None

        self._register_tool()

    def attach_dock(self, dock: Any) -> None:
        self._dock = dock
        if self._tool_def is not None:
            self._tool_def.dock = dock
        self._connect_dock_events()

    # ── Tool Registry ──────────────────────────────────────────────────────────

    def _register_tool(self) -> None:
        try:
            from editor.workspace.tool_registry import ToolDefinition, ToolRegistry
            tool = ToolDefinition(
                id="ui.builder",
                label="UI Builder Visual",
                dock=None,
                shortcuts=["Ctrl+Shift+U"],
                commands=["ui.add_widget", "ui.delete_widget", "ui.export_layout"],
                menu="Interno",
                icon="ui",
                category="Editor",
            )
            ToolRegistry.instance().register(tool)
            self._tool_def = tool
        except Exception:
            self._tool_def = None

    # ── Dock Event Connections ────────────────────────────────────────────────

    def _connect_dock_events(self) -> None:
        if self._dock is None:
            return
        # Conecta seleção da árvore de hierarquia de UI ao SelectionService
        tree = getattr(self._dock, "tree_hierarchy", None)
        if tree is not None:
            try:
                tree.itemSelectionChanged.connect(self._on_ui_tree_selection_changed)
            except Exception:
                pass

    def _on_ui_tree_selection_changed(self) -> None:
        """Propaga a seleção de um widget de UI para o SelectionService."""
        if self._dock is None:
            return
        try:
            tree = self._dock.tree_hierarchy
            items = tree.selectedItems()
            if items:
                widget_name = items[0].text(0)
                # Busca o widget no canvas runtime
                canvas = getattr(self._dock.preview_canvas, "canvas_runtime", None)
                selected_w = None
                if canvas:
                    for child in canvas.children:
                        if child.name == widget_name:
                            selected_w = child
                            break
                if selected_w:
                    self._ctx.selection.select_item(
                        selected_w,
                        type="ui_component",
                        context="ui_builder",
                        id=widget_name,
                    )
        except Exception:
            pass

    # ── Document Management ───────────────────────────────────────────────────

    def open_ui_document(self, path: str | Path | None = None, data: Any = None) -> Any:
        try:
            from editor.workspace.document_framework import DocumentManager, DocumentType
            doc = DocumentManager.instance().open(
                DocumentType.UI,
                path=Path(path) if path else None,
                data=data,
            )
            self._current_document = doc
            return doc
        except Exception:
            return None
