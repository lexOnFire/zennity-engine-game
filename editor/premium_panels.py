from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from editor.premium_editor import HierarchyPanel, InspectorPanel
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.component_commands import AddComponentCommand, RemoveComponentCommand
from engine.core.component_registry import ComponentRegistry, component_registry
from editor.inspector import InspectorPluginRegistry, inspector_plugin_registry


class RealHierarchyPanel(HierarchyPanel):
    """Hierarchy conectada aos GameObjects reais da Viewport."""

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
        name = getattr(obj, "name", str(obj))
        item = QTreeWidgetItem(parent_item, [name])
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
        if root is None:
            return None
        return self._find_item_recursive(root, obj)

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


class RealInspectorPanel(InspectorPanel):
    """Inspector que mostra dados reais do objeto selecionado."""

    def __init__(self) -> None:
        super().__init__()
        self.command_manager: CommandManager | None = None
        self.component_registry: ComponentRegistry = component_registry
        self.inspector_plugin_registry: InspectorPluginRegistry = inspector_plugin_registry
        self.current_object: Any | None = None
        sections = [
            label
            for label in self.findChildren(QLabel)
            if label.objectName() == "InspectorSection"
        ]
        if len(sections) >= 1:
            self.transform_label = sections[0]
        if len(sections) >= 2:
            self.renderer_label = sections[1]
        for section in sections:
            section.setVisible(False)
        self.header = QWidget()
        self.header.setObjectName("InspectorObjectHeader")
        header_layout = QVBoxLayout(self.header)
        header_layout.setContentsMargins(6, 6, 6, 6)
        header_layout.setSpacing(5)

        title_row = QWidget()
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(6)
        self.object_enabled = QCheckBox()
        self.object_enabled.setObjectName("InspectorCheckBox")
        self.object_enabled.setChecked(True)
        self.object_name = QLineEdit()
        self.object_name.setObjectName("InspectorObjectName")
        self.object_static = QCheckBox("Estático")
        self.object_static.setObjectName("InspectorCheckBox")
        title_layout.addWidget(self.object_enabled)
        title_layout.addWidget(self.object_name, 1)
        title_layout.addWidget(self.object_static)

        meta_row = QWidget()
        meta_layout = QHBoxLayout(meta_row)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_layout.setSpacing(6)
        self.object_tag = QComboBox()
        self.object_tag.setObjectName("InspectorCombo")
        self.object_tag.addItems(["Untagged", "Player", "Enemy"])
        self.object_layer = QComboBox()
        self.object_layer.setObjectName("InspectorCombo")
        self.object_layer.addItems(["Default", "UI", "World"])
        meta_layout.addWidget(QLabel("Tag"))
        meta_layout.addWidget(self.object_tag, 1)
        meta_layout.addWidget(QLabel("Layer"))
        meta_layout.addWidget(self.object_layer, 1)

        header_layout.addWidget(title_row)
        header_layout.addWidget(meta_row)
        self.status_label = QLabel("")
        self.status_label.setObjectName("InspectorStatus")
        self.add_component_button = QPushButton("Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        self.add_component_button.clicked.connect(self.open_add_component_menu)
        self.component_list = QWidget()
        self.component_list.setObjectName("InspectorComponentList")
        self.component_list_layout = QVBoxLayout(self.component_list)
        self.component_list_layout.setContentsMargins(4, 4, 4, 4)
        self.component_list_layout.setSpacing(6)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.header)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.component_list)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.status_label)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.add_component_button)

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def set_component_registry(self, registry: ComponentRegistry) -> None:
        self.component_registry = registry

    def set_inspector_plugin_registry(self, registry: InspectorPluginRegistry) -> None:
        self.inspector_plugin_registry = registry

    def load_object(self, obj: Any) -> None:
        self.current_object = obj
        self.status_label.setText("")
        self.add_component_button.setEnabled(obj is not None)
        if obj is None:
            self.header.setEnabled(False)
            self._clear_component_controls()
            self.name.setText("Nenhum objeto selecionado")
            self.object_name.setText("")
            if hasattr(self, "transform_label"):
                self.transform_label.setText("Transform\n  X: 0    Y: 0    Z: 0")
            if hasattr(self, "renderer_label"):
                self.renderer_label.setText("Components\n  Sem componentes")
            return

        name = getattr(obj, "name", str(obj))
        self.name.setText(name)
        self.header.setEnabled(True)
        self.object_name.setText(name)
        self.object_enabled.setChecked(bool(getattr(obj, "active", True)))
        tag = str(getattr(obj, "tag", "Untagged"))
        tag_index = self.object_tag.findText(tag)
        self.object_tag.setCurrentIndex(tag_index if tag_index >= 0 else 0)
        layer = str(getattr(obj, "layer", "Default"))
        layer_index = self.object_layer.findText(layer)
        self.object_layer.setCurrentIndex(layer_index if layer_index >= 0 else 0)
        self.object_static.setChecked(bool(getattr(obj, "is_static", False)))

        components = getattr(obj, "components", [])
        component_names = [
            getattr(comp, "type_name", type(comp).__name__)
            for comp in components
            if not getattr(comp, "required", False)
        ]
        text = ", ".join(component_names) if component_names else "Sem componentes"
        if hasattr(self, "renderer_label"):
            self.renderer_label.setText("Components\n  " + text)
        self._update_legacy_component_labels(components)
        self._render_component_controls(obj)

    def _update_legacy_component_labels(self, components: list[Any]) -> None:
        for component in components:
            if getattr(component, "type_name", type(component).__name__) != "Transform":
                continue
            pos = getattr(component, "position", [0, 0, 0])
            rot = getattr(component, "rotation", [0, 0, 0])
            scale = getattr(component, "scale", [1, 1, 1])
            if hasattr(self, "transform_label"):
                self.transform_label.setText(
                    "Transform\n"
                    f"  Position: X {float(pos[0]):.1f} | Y {float(pos[1]):.1f} | Z {float(pos[2]) if len(pos) > 2 else 0:.1f}\n"
                    f"  Rotation: {list(rot)}\n"
                    f"  Scale: {list(scale)}"
                )
            return

    def _clear_component_controls(self) -> None:
        while self.component_list_layout.count():
            item = self.component_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_component_controls(self, obj: Any) -> None:
        self._clear_component_controls()

        for component in getattr(obj, "components", []):
            plugin = self.inspector_plugin_registry.plugin_for(component)
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            if plugin is None:
                name = QLabel(getattr(component, "type_name", type(component).__name__))
                name.setObjectName("InspectorSection")
                row_layout.addWidget(name, 1)
            else:
                widget = plugin.create_widget(
                    component,
                    self.command_manager,
                    lambda obj=obj: self.load_object(obj),
                )
                row_layout.addWidget(widget, 1)
            if not getattr(component, "required", False):
                remove = QPushButton("×")
                remove.setObjectName("InspectorRemoveComponentButton")
                remove.clicked.connect(
                    lambda checked=False, comp=component: self.remove_component_from_selected(comp)
                )
                row_layout.addWidget(remove)
            self.component_list_layout.addWidget(row)

    def available_component_names(self, include_unavailable: bool = False) -> list[str]:
        if self.current_object is None:
            return []
        names: list[str] = []
        for component_type in self.component_registry.available_components():
            name = str(getattr(component_type, "component_type", component_type.__name__))
            if name == "Component" or getattr(component_type, "required", False):
                continue
            if not include_unavailable and not self.can_add_component(name):
                continue
            names.append(name)
        return names

    def can_add_component(self, component_type: str) -> bool:
        if self.current_object is None:
            return False
        component_class = self.component_registry.resolve(component_type)
        if component_class is None:
            return False
        if str(getattr(component_class, "component_type", component_class.__name__)) == "Component" or getattr(component_class, "required", False):
            return False
        if getattr(component_class, "unique", False):
            return self.current_object.get_component(component_class) is None
        return True

    def open_add_component_menu(self) -> None:
        if self.current_object is None:
            return
        menu = QMenu(self)
        available = self.available_component_names()
        if not available:
            action = menu.addAction("Nenhum componente disponivel")
            action.setEnabled(False)
        for name in available:
            menu.addAction(name, lambda checked=False, value=name: self.add_component_to_selected(value))
        menu.exec(self.add_component_button.mapToGlobal(self.add_component_button.rect().bottomLeft()))

    def add_component_to_selected(self, component_type: str) -> Any:
        if self.current_object is None:
            self.status_label.setText("Nenhum objeto selecionado.")
            return None
        command = AddComponentCommand(self.current_object, component_type, self.component_registry)
        try:
            if self.command_manager is None:
                command.execute()
            else:
                self.command_manager.execute(command)
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return None
        self.load_object(self.current_object)
        return command.component

    def remove_component_from_selected(self, component: Any) -> bool:
        if self.current_object is None:
            self.status_label.setText("Nenhum objeto selecionado.")
            return False
        if component is getattr(self.current_object, "transform", None) or getattr(component, "required", False):
            self.status_label.setText("Transform nao pode ser removido.")
            return False
        command = RemoveComponentCommand(self.current_object, component)
        try:
            if self.command_manager is None:
                command.execute()
            else:
                self.command_manager.execute(command)
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return False
        self.load_object(self.current_object)
        return True

    def set_component_property(self, component: Any, property_name: str, value: Any) -> None:
        plugin = self.inspector_plugin_registry.plugin_for(component)
        if plugin is not None:
            plugin.set_property(
                component,
                property_name,
                value,
                self.command_manager,
                lambda: self.load_object(component.game_object) if getattr(component, "game_object", None) is not None else None,
            )
            return

        old_value = getattr(component, property_name)

        def apply(next_value: Any = value) -> None:
            setattr(component, property_name, next_value)
            if getattr(component, "game_object", None) is not None:
                self.load_object(component.game_object)

        def undo(previous_value: Any = old_value) -> None:
            setattr(component, property_name, previous_value)
            if getattr(component, "game_object", None) is not None:
                self.load_object(component.game_object)

        if self.command_manager is None:
            apply()
            return
        self.command_manager.execute(
            FunctionCommand(
                f"Set {getattr(component, 'type_name', type(component).__name__)}.{property_name}",
                apply,
                undo,
            )
        )
