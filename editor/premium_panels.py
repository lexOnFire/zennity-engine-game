from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem

from editor.premium_editor import HierarchyPanel, InspectorPanel
from editor.runtime.command_manager import CommandManager, FunctionCommand


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
        sections = [
            label
            for label in self.findChildren(QLabel)
            if label.objectName() == "InspectorSection"
        ]
        if len(sections) >= 1:
            self.transform_label = sections[0]
        if len(sections) >= 2:
            self.renderer_label = sections[1]

    def set_command_manager(self, command_manager: CommandManager) -> None:
        self.command_manager = command_manager

    def load_object(self, obj: Any) -> None:
        if obj is None:
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
