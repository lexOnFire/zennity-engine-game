from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
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
from engine.core.component import Component, Transform
from engine.core.component_registry import ComponentRegistry, component_registry


class RealHierarchyPanel(HierarchyPanel):
    """Hierarchy conectada aos GameObjects reais da Viewport."""

    selected = Signal(object)

    def refresh_objects(self, objects: list[Any]) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        root = QTreeWidgetItem(self.tree, ["MainScene"])
        root.setData(0, Qt.UserRole, None)
        for obj in objects:
            name = getattr(obj, "name", str(obj))
            item = QTreeWidgetItem(root, [name])
            item.setData(0, Qt.UserRole, obj)
        root.setExpanded(True)
        self.tree.blockSignals(False)

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
            for index in range(root.childCount()):
                item = root.child(index)
                if item.data(0, Qt.UserRole) is obj:
                    self.tree.setCurrentItem(item)
                    return
        finally:
            self.tree.blockSignals(False)

    def _selected(self) -> None:
        item = self.tree.currentItem()
        self.selected.emit(item.data(0, Qt.UserRole) if item else None)


class RealInspectorPanel(InspectorPanel):
    """Inspector que mostra dados reais do objeto selecionado."""

    def __init__(self) -> None:
        super().__init__()
        self.command_manager: CommandManager | None = None
        self.component_registry: ComponentRegistry = component_registry
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
        self.status_label = QLabel("")
        self.status_label.setObjectName("InspectorSection")
        self.add_component_button = QPushButton("Add Component")
        self.add_component_button.clicked.connect(self.open_add_component_menu)
        self.component_list = QWidget()
        self.component_list_layout = QVBoxLayout(self.component_list)
        self.component_list_layout.setContentsMargins(0, 0, 0, 0)
        self.component_list_layout.setSpacing(4)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.add_component_button)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.component_list)
        self.layout.insertWidget(max(0, self.layout.count() - 1), self.status_label)

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def set_component_registry(self, registry: ComponentRegistry) -> None:
        self.component_registry = registry

    def load_object(self, obj: Any) -> None:
        self.current_object = obj
        self.status_label.setText("")
        self.add_component_button.setEnabled(obj is not None)
        if obj is None:
            self._clear_component_controls()
            self.name.setText("Nenhum objeto selecionado")
            if hasattr(self, "transform_label"):
                self.transform_label.setText("Transform\n  X: 0    Y: 0    Z: 0")
            if hasattr(self, "renderer_label"):
                self.renderer_label.setText("Components\n  Sem componentes")
            return

        name = getattr(obj, "name", str(obj))
        self.name.setText(name)

        transform = getattr(obj, "transform", None)
        if transform is None:
            return

        pos = getattr(transform, "position", [0, 0, 0])
        rot = getattr(transform, "rotation", [0, 0, 0])
        scale = getattr(transform, "scale", [1, 1, 1])

        if hasattr(self, "transform_label"):
            self.transform_label.setText(
                "Transform\n"
                f"  Position: X {float(pos[0]):.1f} | Y {float(pos[1]):.1f} | Z {float(pos[2]) if len(pos) > 2 else 0:.1f}\n"
                f"  Rotation: {list(rot)}\n"
                f"  Scale: {list(scale)}"
            )

        components = getattr(obj, "components", [])
        component_names = [
            getattr(comp, "type_name", type(comp).__name__)
            for comp in components
            if comp is not transform
        ]
        text = ", ".join(component_names) if component_names else "Sem componentes"
        if hasattr(self, "renderer_label"):
            self.renderer_label.setText("Components\n  " + text)
        self._render_component_controls(obj, transform)

    def _clear_component_controls(self) -> None:
        while self.component_list_layout.count():
            item = self.component_list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_component_controls(self, obj: Any, transform: Any) -> None:
        self._clear_component_controls()

        for component in getattr(obj, "components", []):
            if component is transform:
                continue
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            name = QLabel(getattr(component, "type_name", type(component).__name__))
            remove = QPushButton("Remove")
            remove.setEnabled(not getattr(component, "required", False))
            remove.clicked.connect(
                lambda checked=False, comp=component: self.remove_component_from_selected(comp)
            )
            row_layout.addWidget(name, 1)
            row_layout.addWidget(remove)
            self.component_list_layout.addWidget(row)

    def available_component_names(self, include_unavailable: bool = False) -> list[str]:
        if self.current_object is None:
            return []
        names: list[str] = []
        for component_type in self.component_registry.available_components():
            if component_type in {Component, Transform} or getattr(component_type, "required", False):
                continue
            name = str(getattr(component_type, "component_type", component_type.__name__))
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
        if component_class in {Component, Transform} or getattr(component_class, "required", False):
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
