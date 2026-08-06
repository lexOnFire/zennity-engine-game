from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QLineEdit, QMenu, QTreeWidgetItem
from PySide6.QtGui import QDrag

from editor.premium_editor import HierarchyPanel
from editor.premium_panel_base import Panel


class RealHierarchyPanel(HierarchyPanel):
    selected = Signal(object)
    create_empty_requested = Signal()
    duplicate_requested = Signal(object)
    delete_requested = Signal(object)
    rename_requested = Signal(object, str)
    reparent_requested = Signal(object, object, object)
    # Novos sinais de Ponto 5
    group_requested = Signal(list)          # lista de GameObjects → criar grupo
    ungroup_requested = Signal(object)      # objeto grupo → desagrupar filhos
    visibility_toggled = Signal(object, bool)  # objeto, novo estado visible
    lock_toggled = Signal(object, bool)        # objeto, novo estado locked

    # Estado local de visibilidade/lock (indexados por id do objeto)
    _visibility: dict[str, bool]
    _locked: dict[str, bool]
    # CORREÇÃO: Rastreia qual item está sendo arrastado
    _dragged_items: list[QTreeWidgetItem]

    def __init__(self) -> None:
        super().__init__()
        self._visibility = {}
        self._locked = {}
        self._editing_item: QTreeWidgetItem | None = None
        self._dragged_items = []  # Rastreia items em drag
        self.search = self.findChild(QLineEdit)
        if self.search is not None:
            self.search.textChanged.connect(self.filter_tree)

        # Suporte a D&D e Multi-Seleção na hierarquia
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDragDropMode(QAbstractItemView.DragDrop)

        # Colunas extras para visibilidade e lock
        self.tree.setColumnCount(3)
        self.tree.setHeaderHidden(True)
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 22)
        self.tree.setColumnWidth(2, 22)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.itemDoubleClicked.connect(self.begin_rename)
        self.tree.itemChanged.connect(self.on_item_changed)
        # Clique no ícone de olho/cadeado (colunas 1 e 2)
        self.tree.itemClicked.connect(self._on_item_clicked_columns)
        self.tree.itemSelectionChanged.connect(self._selected)

        original_key_press = self.tree.keyPressEvent

        def key_press(event):
            if event.key() == Qt.Key_F2:
                self.begin_rename(self.tree.currentItem(), 0)
                event.accept()
                return
            if event.key() == Qt.Key_Delete:
                selected_items = self.tree.selectedItems()
                objs = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
                for obj in objs:
                    self.delete_requested.emit(obj)
                event.accept()
                return
            if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
                obj = self.current_object()
                if obj is not None:
                    self.duplicate_requested.emit(obj)
                event.accept()
                return
            if event.key() == Qt.Key_G and event.modifiers() & Qt.ControlModifier:
                selected_items = self.tree.selectedItems()
                objs = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
                if objs:
                    self.group_requested.emit(objs)
                event.accept()
                return
            original_key_press(event)

        self.tree.keyPressEvent = key_press

        # CORREÇÃO CRÍTICA: Rastrear qual item está sendo arrastado
        original_start_drag = self.tree.startDrag
        def start_drag(supported_actions):
            """Armazena quais items estão sendo arrastados ANTES do drag começar."""
            self._dragged_items = list(self.tree.selectedItems())
            original_start_drag(supported_actions)
        self.tree.startDrag = start_drag

        original_drop = self.tree.dropEvent

        def drop_event(event):
            # CORREÇÃO: Usar _dragged_items ao invés de selectedItems()
            # porque currentItem() pode ter mudado durante o drag
            dragged_items = self._dragged_items if self._dragged_items else []
            dragged_objs = [it.data(0, Qt.UserRole) for it in dragged_items if it.data(0, Qt.UserRole)]

            # Limpar após usar
            self._dragged_items = []

            if not dragged_objs:
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

            # CORREÇÃO: Quando há múltiplos objetos sendo arrastados,
            # ajustar insert_index para cada um manter a ordem relativa
            for i, dragged in enumerate(dragged_objs):
                adjusted_index = insert_index + i if insert_index is not None else None
                self.reparent_requested.emit(dragged, parent_obj, adjusted_index)
            event.acceptProposedAction()

        self.tree.dropEvent = drop_event

    # ── Construção da árvore ───────────────────────────────────────────────

    def refresh_objects(self, objects: list[Any]) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, ["MainScene", "", ""])
        root.setData(0, Qt.UserRole, None)
        for obj in objects:
            if getattr(obj, "parent", None) is None:
                self._add_object_item(root, obj)
        root.setExpanded(True)
        self.tree.blockSignals(False)
        self.filter_tree(self.search.text() if self.search is not None else "")

    def _add_object_item(self, parent_item: QTreeWidgetItem, obj: Any) -> QTreeWidgetItem:
        obj_id = str(getattr(obj, "id", id(obj)))
        is_visible = self._visibility.get(obj_id, True)
        is_locked  = self._locked.get(obj_id, False)
        is_prefab  = bool(getattr(obj, "prefab_source", None))
        is_group   = getattr(obj, "is_group", False)

        # Ícone prefix por tipo
        name = getattr(obj, "name", str(obj))
        name_lower = name.lower()
        if is_group:
            prefix = "📂 "
        elif is_prefab:
            prefix = "🔷 "
        elif "camera" in name_lower:
            prefix = "📷 "
        elif "light" in name_lower:
            prefix = "💡 "
        else:
            prefix = "📦 "

        label = f"{prefix}{name}"
        vis_icon  = "👁" if is_visible else "🚫"
        lock_icon = "🔒" if is_locked  else "  "

        item = QTreeWidgetItem(parent_item, [label, vis_icon, lock_icon])
        item.setData(0, Qt.UserRole, obj)
        item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        item.setTextAlignment(1, Qt.AlignCenter)
        item.setTextAlignment(2, Qt.AlignCenter)

        # Cor diferenciada para prefabs e objetos locked
        if is_prefab:
            from PySide6.QtGui import QColor
            item.setForeground(0, QColor("#5ab5ff"))
        if not is_visible:
            from PySide6.QtGui import QColor
            item.setForeground(0, QColor("#666666"))

        for child in getattr(obj, "children", []):
            self._add_object_item(item, child)
        item.setExpanded(True)
        return item

    def _on_item_clicked_columns(self, item: QTreeWidgetItem, column: int) -> None:
        """Trata clique nas colunas de visibilidade (1) e lock (2)."""
        obj = item.data(0, Qt.UserRole)
        if obj is None:
            return
        obj_id = str(getattr(obj, "id", id(obj)))

        if column == 1:
            new_vis = not self._visibility.get(obj_id, True)
            self._visibility[obj_id] = new_vis
            item.setText(1, "👁" if new_vis else "🚫")
            from PySide6.QtGui import QColor
            item.setForeground(0, QColor("#e0e0e0") if new_vis else QColor("#666666"))
            self.visibility_toggled.emit(obj, new_vis)

        elif column == 2:
            new_lock = not self._locked.get(obj_id, False)
            self._locked[obj_id] = new_lock
            item.setText(2, "🔒" if new_lock else "  ")
            self.lock_toggled.emit(obj, new_lock)

    # ── Seleção ────────────────────────────────────────────────────────────

    def select_object(self, obj: Any) -> None:
        root = self.tree.topLevelItem(0)
        if root is None:
            return
        # Se o objeto já estiver entre os selecionados, preserva a multi-seleção atual
        selected_items = self.tree.selectedItems()
        selected_objs = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
        if obj in selected_objs and len(selected_objs) > 1:
            return

        self.tree.blockSignals(True)
        try:
            self.tree.clearSelection()
            self.tree.setCurrentItem(None)
            if obj is None:
                return
            item = self.find_item(obj)
            if item is not None:
                item.setSelected(True)
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

    # ── Renomeação ─────────────────────────────────────────────────────────

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

    # ── Menu de Contexto ───────────────────────────────────────────────────

    def open_context_menu(self, pos) -> None:
        menu = QMenu(self)
        create_action  = menu.addAction("Create Empty")
        menu.addSeparator()
        duplicate_action = menu.addAction("Duplicate  (Ctrl+D)")
        delete_action    = menu.addAction("Delete  (Del)")
        rename_action    = menu.addAction("Rename  (F2)")
        menu.addSeparator()

        selected_items = self.tree.selectedItems()
        multi_objs = [it.data(0, Qt.UserRole) for it in selected_items if it.data(0, Qt.UserRole)]
        group_action   = menu.addAction(f"Group Selection ({len(multi_objs)})  (Ctrl+G)")
        group_action.setEnabled(len(multi_objs) > 1)
        obj = self.current_object()
        ungroup_action = menu.addAction("Ungroup")
        ungroup_action.setEnabled(obj is not None and getattr(obj, "is_group", False))

        menu.addSeparator()
        expand_action   = menu.addAction("Expand All")
        collapse_action = menu.addAction("Collapse All")

        duplicate_action.setEnabled(obj is not None)
        delete_action.setEnabled(len(multi_objs) > 0)
        rename_action.setEnabled(obj is not None)

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if action is create_action:
            self.create_empty_requested.emit()
        elif action is duplicate_action and obj is not None:
            self.duplicate_requested.emit(obj)
        elif action is delete_action:
            for o in multi_objs:
                self.delete_requested.emit(o)
        elif action is rename_action:
            self.begin_rename(self.tree.currentItem(), 0)
        elif action is group_action:
            self.group_requested.emit(multi_objs)
        elif action is ungroup_action and obj is not None:
            self.ungroup_requested.emit(obj)
        elif action is expand_action:
            self.tree.expandAll()
        elif action is collapse_action:
            root = self.tree.topLevelItem(0)
            self.tree.collapseAll()
            if root is not None:
                root.setExpanded(True)

    # ── Filtro de Pesquisa ─────────────────────────────────────────────────

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

