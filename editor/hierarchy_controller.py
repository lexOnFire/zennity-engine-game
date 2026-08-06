"""Hierarchy interaction and editor-selection coordination."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMenu, QTreeWidget, QTreeWidgetItem

from editor.hierarchy_view_renderer import HierarchyViewRenderer


class HierarchyController:
    """Owns hierarchy signals, context actions and selection synchronization."""

    def __init__(self, host: Any, renderer: HierarchyViewRenderer | None = None) -> None:
        self.host = host
        self.renderer = renderer or HierarchyViewRenderer(host)
        self._connected = False
        self._connections: list[tuple[Any, Any]] = []

    def _bind(self, signal: Any, callback: Any) -> None:
        signal.connect(callback)
        self._connections.append((signal, callback))

    def disconnect(self) -> bool:
        if not self._connected:
            return False
        for signal, callback in reversed(self._connections):
            signal.disconnect(callback)
        self._connections.clear()
        self._connected = False
        return True

    def connect(self) -> bool:
        if self._connected:
            return False
        h = self.host
        h.hierarchy_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        h.hierarchy_tree.setDragEnabled(True)
        h.hierarchy_tree.setAcceptDrops(True)
        h.hierarchy_tree.setDragDropMode(QTreeWidget.InternalMove)
        self._bind(h.hierarchy_tree.itemSelectionChanged, self._on_selection_changed)
        self._bind(h.hierarchy_tree.itemDoubleClicked, 
            lambda item: h._rename_object(self.item_name(item))
        )
        h.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._bind(h.hierarchy_tree.customContextMenuRequested, h._open_hierarchy_menu)
        
        # Conectar atalho da tecla Delete/Backspace e Ctrl+G na árvore de hierarquia
        orig_key_press = h.hierarchy_tree.keyPressEvent
        def hierarchy_key_press(event) -> None:
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                if h._selected_name is not None and not h._play_session.is_running:
                    h._scene_objects.delete(h._selected_name)
                    return
            if event.key() == Qt.Key_G and (event.modifiers() & Qt.ControlModifier):
                selected_items = h.hierarchy_tree.selectedItems()
                selected_names = [self.item_name(it) for it in selected_items if self.item_name(it)]
                if len(selected_names) > 1 and hasattr(h, "_group_objects"):
                    h._group_objects(selected_names)
                    return
            orig_key_press(event)
        h.hierarchy_tree.keyPressEvent = hierarchy_key_press

        self._connected = True
        return True

    def open_context_menu(self, position) -> None:
        h = self.host
        item = h.hierarchy_tree.itemAt(position)
        item_name = self.item_name(item)
        if item is None or item_name not in h._objects_by_name:
            return
        menu = QMenu(h)
        rename_action = menu.addAction("Renomear")
        duplicate_action = menu.addAction("Duplicar")
        locked = bool(h._objects_by_name[item_name].get("editor_locked", False))
        lock_action = menu.addAction("Destravar transformação" if locked else "Travar transformação")
        prefab_action = menu.addAction("Criar Prefab")
        delete_action = menu.addAction("Excluir")
        selected_items = h.hierarchy_tree.selectedItems()
        selected_names = [self.item_name(it) for it in selected_items if self.item_name(it)]
        group_action = menu.addAction(f"Group Selection ({len(selected_names)})")
        group_action.setEnabled(len(selected_names) > 1)
        group_action.triggered.connect(lambda _checked=False: hasattr(h, "_group_objects") and h._group_objects(selected_names))

        rename_action.triggered.connect(lambda _checked=False: h._rename_object(item_name))
        duplicate_action.triggered.connect(
            lambda _checked=False: self.select_and_duplicate(item_name)
        )
        lock_action.triggered.connect(
            lambda _checked=False: h._scene_objects.set_transform_locked(item_name, not locked)
        )
        prefab_action.triggered.connect(
            lambda _checked=False: self.select_and_save_prefab(item_name)
        )
        delete_action.triggered.connect(lambda _checked=False: h._scene_objects.delete(item_name))
        menu.exec(h.hierarchy_tree.viewport().mapToGlobal(position))

    def select_and_duplicate(self, name: str) -> None:
        if self.host._selection.select_for_action(name):
            self.host._scene_objects.duplicate_selected()

    def select_and_save_prefab(self, name: str) -> None:
        if self.host._selection.select_for_action(name):
            self.host._prefab_workspace.save_selected()

    def _on_selection_changed(self) -> None:
        h = self.host
        selected_items = h.hierarchy_tree.selectedItems()
        if not selected_items:
            h._selection.select(None)
            return
        selected_names = [self.item_name(it) for it in selected_items if self.item_name(it)]
        h._selected_names = selected_names
        # Seleciona o principal no Inspector
        name = selected_names[0]
        in_scene = name in h._objects_by_name
        in_runtime = h._runtime_playing and name in h._runtime_objects_by_name
        if in_scene or in_runtime:
            source = "Runtime" if in_runtime and not in_scene else "Interface"
            h._selection.select(name, source=source)

    def select_item(self, item: QTreeWidgetItem) -> None:
        h = self.host
        name = self.item_name(item)
        in_scene = name in h._objects_by_name
        in_runtime = h._runtime_playing and name in h._runtime_objects_by_name
        if not (in_scene or in_runtime):
            return
        source = "Runtime" if in_runtime and not in_scene else "Interface"
        h._selection.select(name, source=source)

    def refresh(self, *, force: bool = False) -> bool:
        return self.renderer.refresh(force=force)

    def item_name(self, item: QTreeWidgetItem | None) -> str:
        return self.renderer.item_name(item)
