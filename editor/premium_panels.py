from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFrame,
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
        self.component_foldouts: dict[str, bool] = {}
        self.component_clipboard: dict[str, Any] | None = None
        self.selected_component: Any | None = None
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
        self.component_filter = QLineEdit()
        self.component_filter.setObjectName("InspectorComponentFilter")
        self.component_filter.setPlaceholderText("Filtrar componentes...")
        self.component_filter.textChanged.connect(self.apply_component_filter)
        self.add_component_button = QPushButton("Adicionar Componente")
        self.add_component_button.setObjectName("InspectorAddComponentButton")
        self.add_component_button.clicked.connect(self.open_add_component_menu)
        self.component_list = QWidget()
        self.component_list.setObjectName("InspectorComponentList")
        self.component_list_layout = QVBoxLayout(self.component_list)
        self.component_list_layout.setContentsMargins(4, 4, 4, 4)
        self.component_list_layout.setSpacing(6)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.header)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.component_filter)
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
        self.component_filter.setEnabled(obj is not None)
        if obj is None:
            self.header.setEnabled(False)
            self._clear_component_controls()
            self.name.setText("Nenhum objeto selecionado")
            self.object_name.setText("")
            self.component_filter.clear()
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
            if not self._component_matches_filter(component):
                continue
            plugin = self.inspector_plugin_registry.plugin_for(component)
            row = self._create_component_shell(component)
            body = row.findChild(QWidget, "InspectorComponentBody")
            body_layout = body.layout() if body is not None else None
            if plugin is None:
                name = QLabel(getattr(component, "type_name", type(component).__name__))
                name.setObjectName("InspectorSection")
                if body_layout is not None:
                    body_layout.addWidget(name)
            else:
                widget = plugin.create_widget(
                    component,
                    self.command_manager,
                    lambda obj=obj: self.load_object(obj),
                )
                if body_layout is not None:
                    body_layout.addWidget(widget)
            self.component_list_layout.addWidget(row)

    def _create_component_shell(self, component: Any) -> QFrame:
        type_name = self._component_type(component)
        key = self._component_key(component)
        is_open = self.component_foldouts.get(key, True)
        shell = QFrame()
        shell.setObjectName("InspectorComponentShell")
        shell.setProperty("component_type", type_name)
        shell.setProperty("component_id", key)
        shell.setProperty("selected", component is self.selected_component)
        shell.setProperty("disabled", not bool(getattr(component, "enabled", True)))
        shell.setContextMenuPolicy(Qt.CustomContextMenu)
        shell.customContextMenuRequested.connect(
            lambda pos, comp=component, frame=shell: self.open_component_context_menu(comp, frame.mapToGlobal(pos))
        )
        layout = QVBoxLayout(shell)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        header = QWidget()
        header.setObjectName("InspectorComponentHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        toggle = QPushButton("v" if is_open else ">")
        toggle.setObjectName("InspectorFoldoutButton")
        toggle.setFixedWidth(24)
        toggle.clicked.connect(lambda checked=False, comp=component: self.toggle_component_foldout(comp))
        icon = QLabel(self._component_icon(type_name))
        icon.setObjectName("InspectorComponentIcon")
        title = QLabel(type_name)
        title.setObjectName("InspectorComponentTitle")
        if not getattr(component, "enabled", True):
            title.setText(f"{type_name} (desabilitado)")
        title.mousePressEvent = lambda event, comp=component: self.select_component(comp)
        menu_button = QPushButton("...")
        menu_button.setObjectName("InspectorComponentMenuButton")
        menu_button.setFixedWidth(28)
        menu_button.clicked.connect(
            lambda checked=False, comp=component, button=menu_button: self.open_component_context_menu(
                comp,
                button.mapToGlobal(button.rect().bottomLeft()),
            )
        )

        header_layout.addWidget(toggle)
        header_layout.addWidget(icon)
        header_layout.addWidget(title, 1)
        header_layout.addWidget(menu_button)
        layout.addWidget(header)

        body = QWidget()
        body.setObjectName("InspectorComponentBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(4)
        body.setVisible(is_open)
        layout.addWidget(body)
        return shell

    def _component_type(self, component: Any) -> str:
        return str(getattr(component, "type_name", type(component).__name__))

    def _component_key(self, component: Any) -> str:
        return str(getattr(component, "id", id(component)))

    def _component_icon(self, type_name: str) -> str:
        icons = {
            "Transform": "T",
            "RigidBody": "R",
            "BoxCollider": "C",
            "CircleCollider": "C",
            "Script": "S",
            "Camera": "M",
            "AudioSource": "A",
            "Animator": "N",
        }
        return icons.get(type_name, type_name[:1].upper() if type_name else "?")

    def _component_matches_filter(self, component: Any) -> bool:
        query = self.component_filter.text().strip().lower()
        if not query:
            return True
        return query in self._component_type(component).lower()

    def apply_component_filter(self, _text: str = "") -> None:
        if self.current_object is not None:
            self._render_component_controls(self.current_object)

    def select_component(self, component: Any) -> None:
        self.selected_component = component
        if self.current_object is not None:
            self._render_component_controls(self.current_object)

    def toggle_component_foldout(self, component: Any) -> bool:
        key = self._component_key(component)
        next_state = not self.component_foldouts.get(key, True)
        self.component_foldouts[key] = next_state
        if self.current_object is not None:
            self._render_component_controls(self.current_object)
        return next_state

    def open_component_context_menu(self, component: Any, global_pos) -> None:
        menu = QMenu(self)
        reset = menu.addAction("Reset")
        copy = menu.addAction("Copy")
        paste = menu.addAction("Paste Values")
        remove = menu.addAction("Remove")
        menu.addSeparator()
        move_up = menu.addAction("Move Up")
        move_down = menu.addAction("Move Down")
        paste.setEnabled(self.can_paste_component_values(component))
        remove.setEnabled(not getattr(component, "required", False))
        action = menu.exec(global_pos)
        if action is reset:
            self.reset_component(component)
        elif action is copy:
            self.copy_component(component)
        elif action is paste:
            self.paste_component_values(component)
        elif action is remove:
            self.remove_component_from_selected(component)
        elif action is move_up:
            self.move_component_visual(component, -1)
        elif action is move_down:
            self.move_component_visual(component, 1)

    def copy_component(self, component: Any) -> dict[str, Any] | None:
        if not hasattr(component, "serialize"):
            self.status_label.setText("Componente nao pode ser copiado.")
            return None
        self.component_clipboard = deepcopy(component.serialize())
        self.status_label.setText(f"Componente {self._component_type(component)} copiado.")
        return self.component_clipboard

    def can_paste_component_values(self, component: Any) -> bool:
        return (
            self.component_clipboard is not None
            and self.component_clipboard.get("type") == self._component_type(component)
            and hasattr(component, "deserialize_properties")
        )

    def paste_component_values(self, component: Any) -> bool:
        if not self.can_paste_component_values(component):
            self.status_label.setText("Nao ha valores compativeis para colar.")
            return False
        assert self.component_clipboard is not None
        before = deepcopy(component.serialize())
        after = deepcopy(self.component_clipboard)
        after["id"] = getattr(component, "id", after.get("id"))

        def apply() -> None:
            self._apply_component_snapshot(component, after)
            if self.current_object is not None:
                self.load_object(self.current_object)

        def undo() -> None:
            self._apply_component_snapshot(component, before)
            if self.current_object is not None:
                self.load_object(self.current_object)

        self._execute_component_ux_command(
            f"Paste {self._component_type(component)} Values",
            apply,
            undo,
        )
        return True

    def reset_component(self, component: Any) -> bool:
        component_class = self.component_registry.resolve(self._component_type(component)) or type(component)
        try:
            default_component = component_class()
        except Exception as exc:
            self.status_label.setText(f"Reset indisponivel: {exc}")
            return False
        before = deepcopy(component.serialize())
        after = deepcopy(default_component.serialize())
        after["id"] = getattr(component, "id", after.get("id"))

        def apply() -> None:
            self._apply_component_snapshot(component, after)
            if self.current_object is not None:
                self.load_object(self.current_object)

        def undo() -> None:
            self._apply_component_snapshot(component, before)
            if self.current_object is not None:
                self.load_object(self.current_object)

        self._execute_component_ux_command(
            f"Reset {self._component_type(component)}",
            apply,
            undo,
        )
        return True

    def move_component_visual(self, component: Any, offset: int) -> bool:
        if self.current_object is None or component not in getattr(self.current_object, "components", []):
            return False
        components = self.current_object.components
        old_index = components.index(component)
        new_index = max(0, min(len(components) - 1, old_index + offset))
        if old_index == new_index:
            return False

        def move(src: int, dst: int) -> None:
            item = components.pop(src)
            components.insert(dst, item)
            self.load_object(self.current_object)

        self._execute_component_ux_command(
            f"Move {self._component_type(component)}",
            lambda: move(old_index, new_index),
            lambda: move(new_index, old_index),
        )
        return True

    def _apply_component_snapshot(self, component: Any, data: dict[str, Any]) -> None:
        if "enabled" in data:
            component.enabled = bool(data.get("enabled", True))
        if data.get("id"):
            component.id = str(data["id"])
        properties = data.get("properties", {})
        if isinstance(properties, dict) and hasattr(component, "deserialize_properties"):
            component.deserialize_properties(deepcopy(properties))

    def _execute_component_ux_command(self, description: str, apply, undo) -> None:
        if self.command_manager is None:
            apply()
            return
        self.command_manager.execute(FunctionCommand(description, apply, undo))

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
