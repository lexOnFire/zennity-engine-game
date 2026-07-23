from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QLineEdit, QMenu, QTreeWidgetItem

from editor.premium_editor import HierarchyPanel
from editor.premium_panel_base import Panel


class RealHierarchyPanel(HierarchyPanel):
    selected = Signal(object)
    create_empty_requested = Signal()
    duplicate_requested = Signal(object)
    delete_requested = Signal(object)
    rename_requested = Signal(object, str)
    reparent_requested = Signal(object, object, object)

    def __init__(self) -> None:
        super().__init__()
        self._editing_item: QTreeWidgetItem | None = None
        self.search = self.findChild(QLineEdit)
        if self.search is not None:
            self.search.textChanged.connect(self.filter_tree)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDrop)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.itemDoubleClicked.connect(self.begin_rename)
        self.tree.itemChanged.connect(self.on_item_changed)

        original_key_press = self.tree.keyPressEvent

        def key_press(event):
            if event.key() == Qt.Key_F2:
                self.begin_rename(self.tree.currentItem(), 0)
                event.accept()
                return
            if event.key() == Qt.Key_Delete:
                obj = self.current_object()
                if obj is not None:
                    self.delete_requested.emit(obj)
                event.accept()
                return
            if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
                obj = self.current_object()
                if obj is not None:
                    self.duplicate_requested.emit(obj)
                event.accept()
                return
            original_key_press(event)

        self.tree.keyPressEvent = key_press
        original_drop = self.tree.dropEvent

        def drop_event(event):
            dragged = self.current_object()
            if dragged is None:
                original_drop(event)
                return
            target_item = self.tree.itemAt(event.position().toPoint()) if hasattr(event, "position") else self.tree.itemAt(event.pos())
            parent_obj = None
            insert_index = None
            if target_item is not None:
                target_obj = target_item.data(0, Qt.UserRole)
                indicator = self.tree.dropIndicatorPosition()
                if indicator == QAbstractItemView.DropIndicatorPosition.OnItem and target_obj is not None:
                    parent_obj = target_obj
                else:
                    parent_item = target_item.parent()
                    parent_obj = parent_item.data(0, Qt.UserRole) if parent_item is not None else None
                    sibling_parent = parent_item if parent_item is not None else self.tree.invisibleRootItem()
                    insert_index = sibling_parent.indexOfChild(target_item)
                    if indicator == QAbstractItemView.DropIndicatorPosition.BelowItem:
                        insert_index += 1
            self.reparent_requested.emit(dragged, parent_obj, insert_index)
            event.acceptProposedAction()

        self.tree.dropEvent = drop_event

    def refresh_objects(self, objects: list[Any]) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, ["MainScene"])
        root.setData(0, Qt.UserRole, None)
        for obj in objects:
            if getattr(obj, "parent", None) is None:
                self._add_object_item(root, obj)
        root.setExpanded(True)
        self.tree.blockSignals(False)
        self.filter_tree(self.search.text() if self.search is not None else "")

    def _add_object_item(self, parent_item: QTreeWidgetItem, obj: Any) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parent_item, [getattr(obj, "name", str(obj))])
        item.setData(0, Qt.UserRole, obj)
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        for child in getattr(obj, "children", []):
            self._add_object_item(item, child)
        item.setExpanded(True)
        return item

    def select_object(self, obj: Any) -> None:
        root = self.tree.topLevelItem(0)
        if root is None:
            return
        self.tree.blockSignals(True)
        try:
            self.tree.clearSelection()
            self.tree.setCurrentItem(None)
            if obj is None:
                return
            item = self.find_item(obj)
            if item is not None:
                self.tree.setCurrentItem(item)
                parent = item.parent()
                while parent is not None:
                    parent.setExpanded(True)
                    parent = parent.parent()
        finally:
            self.tree.blockSignals(False)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        self.selected.emit(item.data(0, Qt.UserRole) if item else None)

    def current_object(self) -> Any:
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item is not None else None

    def find_item(self, obj: Any) -> QTreeWidgetItem | None:
        root = self.tree.topLevelItem(0)
        return None if root is None else self._find_item_recursive(root, obj)

    def _find_item_recursive(self, item: QTreeWidgetItem, obj: Any) -> QTreeWidgetItem | None:
        if item.data(0, Qt.UserRole) is obj:
            return item
        for index in range(item.childCount()):
            found = self._find_item_recursive(item.child(index), obj)
            if found is not None:
                return found
        return None

    def begin_rename(self, item: QTreeWidgetItem | None, column: int = 0) -> None:
        if item is None or item.data(0, Qt.UserRole) is None:
            return
        self._editing_item = item
        self.tree.editItem(item, column)

    def on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        obj = item.data(0, Qt.UserRole)
        if obj is None:
            return
        new_name = item.text(0).strip()
        if not new_name:
            self.tree.blockSignals(True)
            item.setText(0, getattr(obj, "name", "GameObject"))
            self.tree.blockSignals(False)
            return
        if new_name != getattr(obj, "name", ""):
            self.rename_requested.emit(obj, new_name)

    def open_context_menu(self, pos) -> None:
        menu = QMenu(self)
        create_action = menu.addAction("Create Empty")
        duplicate_action = menu.addAction("Duplicate")
        delete_action = menu.addAction("Delete")
        rename_action = menu.addAction("Rename")
        menu.addSeparator()
        expand_action = menu.addAction("Expand All")
        collapse_action = menu.addAction("Collapse All")
        obj = self.current_object()
        duplicate_action.setEnabled(obj is not None)
        delete_action.setEnabled(obj is not None)
        rename_action.setEnabled(obj is not None)
        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action is create_action:
            self.create_empty_requested.emit()
        elif action is duplicate_action and obj is not None:
            self.duplicate_requested.emit(obj)
        elif action is delete_action and obj is not None:
            self.delete_requested.emit(obj)
        elif action is rename_action:
            self.begin_rename(self.tree.currentItem(), 0)
        elif action is expand_action:
            self.tree.expandAll()
        elif action is collapse_action:
            root = self.tree.topLevelItem(0)
            self.tree.collapseAll()
            if root is not None:
                root.setExpanded(True)

    def filter_tree(self, text: str) -> None:
        root = self.tree.topLevelItem(0)
        if root is None:
            return
        query = text.strip().lower()
        if not query:
            self._set_visible_recursive(root, True)
            root.setExpanded(True)
            return
        self._filter_item_recursive(root, query)
        root.setHidden(False)
        root.setExpanded(True)

    def _set_visible_recursive(self, item: QTreeWidgetItem, visible: bool) -> None:
        item.setHidden(not visible)
        for index in range(item.childCount()):
            self._set_visible_recursive(item.child(index), visible)

    def _filter_item_recursive(self, item: QTreeWidgetItem, query: str) -> bool:
        obj = item.data(0, Qt.UserRole)
        own_match = query in item.text(0).lower() if obj is not None else False
        child_match = False
        for index in range(item.childCount()):
            child_match = self._filter_item_recursive(item.child(index), query) or child_match
        visible = own_match or child_match or obj is None
        item.setHidden(not visible)
        if child_match:
            item.setExpanded(True)
        return visible
