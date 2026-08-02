"""ReactiveEditorBridge — Sprint 4a: integração reativa Hierarchy → Scene → Inspector → Viewport.

Este módulo conecta o SelectionService centralizado com os 4 painéis
base do editor de forma reativa (sem polling):

  SelectionService (SelectionItem genérico)
        ↓
    HierarchyDock   ← destaca o item selecionado
    InspectorDock   ← carrega propriedades do objeto selecionado
    Viewport        ← foca/gizmo no objeto selecionado
    SceneViewModel  ← mantém sinais Qt compatíveis

Quando qualquer painel muda a seleção, o SelectionService emite
EVENT_SELECTION_CHANGED e todos os outros painéis se atualizam
automaticamente via EventBus (domínio Selection.*).
"""
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


class ReactiveEditorBridge:
    """Conecta o SelectionService com os painéis base de forma reativa.

    Uso:
        bridge = ReactiveEditorBridge(editor_context)
        bridge.attach_hierarchy(dock_hierarchy)
        bridge.attach_inspector(dock_inspector)
        bridge.attach_viewport(viewport)
        bridge.attach_viewmodel(scene_viewmodel)
    """

    def __init__(self, editor_context: Any) -> None:
        self._ctx = editor_context
        self._selection = editor_context.selection
        self._hierarchy: Any = None
        self._inspector: Any = None
        self._viewport: Any = None
        self._viewmodel: Any = None
        self._suppressing = False

        # Subscreve no SelectionService para propagar a todos
        self._selection.subscribe(self._on_selection_changed)

        # Subscreve no EventBus de domínio Scene.* para atualizar hierarquia
        try:
            from editor.core.event_bus import EventBus, EVENT_OBJECT_CREATED, EVENT_OBJECT_DELETED, EVENT_HIERARCHY_UPDATED
            EventBus.subscribe(EVENT_OBJECT_CREATED, self._on_scene_hierarchy_changed)
            EventBus.subscribe(EVENT_OBJECT_DELETED, self._on_scene_hierarchy_changed)
            EventBus.subscribe(EVENT_HIERARCHY_UPDATED, self._on_scene_hierarchy_changed)
        except Exception:
            logger.debug(
                "ReactiveEditorBridge: falha ao assinar eventos de hierarquia.",
                exc_info=True,
            )

    # ── Attach ────────────────────────────────────────────────────────────────

    def attach_hierarchy(self, hierarchy_dock: Any) -> None:
        self._hierarchy = hierarchy_dock
        # Quando o usuário clica na hierarquia, notifica o SelectionService
        _patch_hierarchy_selection(hierarchy_dock, self._selection)

    def attach_inspector(self, inspector_dock: Any) -> None:
        self._inspector = inspector_dock

    def attach_viewport(self, viewport: Any) -> None:
        self._viewport = viewport

    def attach_viewmodel(self, viewmodel: Any) -> None:
        self._viewmodel = viewmodel

    # ── Handlers reativos ──────────────────────────────────────────────────────

    def _on_selection_changed(self, obj: Any) -> None:
        """Propaga seleção para todos os painéis registrados."""
        if self._suppressing:
            return
        self._suppressing = True
        try:
            self._sync_hierarchy(obj)
            self._sync_inspector(obj)
            self._sync_viewport(obj)
            self._sync_viewmodel(obj)
        finally:
            self._suppressing = False

    def _sync_hierarchy(self, obj: Any) -> None:
        if self._hierarchy is None:
            return
        try:
            # HierarchyDock expõe select_object_in_tree(obj)
            if hasattr(self._hierarchy, "select_object_in_tree"):
                self._hierarchy.select_object_in_tree(obj)
        except Exception:
            logger.debug(
                "ReactiveEditorBridge: falha ao sincronizar a Hierarchy.",
                exc_info=True,
            )

    def _sync_inspector(self, obj: Any) -> None:
        if self._inspector is None:
            return
        try:
            if hasattr(self._inspector, "load_object"):
                self._inspector.load_object(obj)
        except Exception:
            logger.debug(
                "ReactiveEditorBridge: falha ao sincronizar o Inspector.",
                exc_info=True,
            )

    def _sync_viewport(self, obj: Any) -> None:
        if self._viewport is None:
            return
        try:
            if hasattr(self._viewport, "select_object"):
                self._viewport.select_object(obj)
            elif hasattr(self._viewport, "set_selected"):
                self._viewport.set_selected(obj)
        except Exception:
            pass

    def _sync_viewmodel(self, obj: Any) -> None:
        if self._viewmodel is None:
            return
        try:
            if hasattr(self._viewmodel, "_apply_selection"):
                self._viewmodel._apply_selection(obj)
        except Exception:
            pass

    def _on_scene_hierarchy_changed(self, **kwargs: Any) -> None:
        """Atualiza a hierarquia quando objetos são adicionados/removidos da cena."""
        if self._hierarchy is None:
            return
        try:
            if hasattr(self._hierarchy, "populate_tree"):
                self._hierarchy.populate_tree()
        except Exception:
            pass

    def select(self, obj: Any, context: str = "scene") -> None:
        """API pública para selecionar um objeto e propagar para todos os painéis."""
        self._selection.select_item(obj, type="game_object", context=context)


def _patch_hierarchy_selection(hierarchy_dock: Any, selection_service: Any) -> None:
    """Monkey-patch para conectar a seleção da HierarchyDock ao SelectionService."""
    original_handler = getattr(hierarchy_dock, "on_item_selection_changed", None)
    if original_handler is None:
        return

    def patched_handler() -> None:
        try:
            selected_items = hierarchy_dock.tree.selectedItems()
            if selected_items:
                from PySide6.QtCore import Qt
                obj = selected_items[0].data(0, Qt.UserRole)
                selection_service.select_item(obj, type="game_object", context="hierarchy")
            else:
                selection_service.clear_selection()
        except Exception:
            if original_handler:
                original_handler()

    try:
        hierarchy_dock.tree.itemSelectionChanged.disconnect(original_handler)
        hierarchy_dock.tree.itemSelectionChanged.connect(patched_handler)
        hierarchy_dock._reactive_selection_handler = patched_handler
    except Exception:
        logger.debug(
            "ReactiveEditorBridge: falha ao instalar o handler reativo da Hierarchy.",
            exc_info=True,
        )
