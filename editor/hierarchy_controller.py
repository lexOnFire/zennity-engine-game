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

    def connect(self) -> bool:
        if self._connected:
            return False
        h = self.host
        h.hierarchy_tree.setDragEnabled(True)
        h.hierarchy_tree.setAcceptDrops(True)
        h.hierarchy_tree.setDragDropMode(QTreeWidget.InternalMove)
        h.hierarchy_tree.itemClicked.connect(h._select_hierarchy_item)
        h.hierarchy_tree.itemDoubleClicked.connect(
            lambda item: h._rename_object(self.item_name(item))
        )
        h.hierarchy_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        h.hierarchy_tree.customContextMenuRequested.connect(h._open_hierarchy_menu)
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
        prefab_action = menu.addAction("Criar Prefab")
        delete_action = menu.addAction("Excluir")
        rename_action.triggered.connect(lambda _checked=False: h._rename_object(item_name))
        duplicate_action.triggered.connect(
            lambda _checked=False: self.select_and_duplicate(item_name)
        )
        prefab_action.triggered.connect(
            lambda _checked=False: self.select_and_save_prefab(item_name)
        )
        delete_action.triggered.connect(lambda _checked=False: h._delete_object(item_name))
        menu.exec(h.hierarchy_tree.viewport().mapToGlobal(position))

    def select_and_duplicate(self, name: str) -> None:
        self.host._selected_name = name
        self.host._scene_objects.duplicate_selected()

    def select_and_save_prefab(self, name: str) -> None:
        self.host._selected_name = name
        self.host._save_selected_as_prefab()

    def select_item(self, item: QTreeWidgetItem) -> None:
        h = self.host
        name = self.item_name(item)
        in_scene = name in h._objects_by_name
        in_runtime = h._runtime_playing and name in h._runtime_objects_by_name
        if not (in_scene or in_runtime):
            return
        h._scene_controller.select(name)
        h._selected_name = name
        h._update_inspector(name)
        source = "Runtime" if in_runtime and not in_scene else "Interface"
        h.statusBar().showMessage(f"{source}: {name} selecionado")

    def refresh(self, *, force: bool = False) -> bool:
        return self.renderer.refresh(force=force)

    def item_name(self, item: QTreeWidgetItem | None) -> str:
        return self.renderer.item_name(item)
