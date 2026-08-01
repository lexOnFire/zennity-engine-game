from __future__ import annotations
from typing import Any
from pathlib import Path
from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.inspector.plugin_ui_utils import *
from editor.ui.property_editors import DragScrubSlider

class TransformInspectorPlugin(InspectorPlugin):
    component_type = "Transform"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, body = _section("Transform")
        fields: dict[tuple[str, int], QDoubleSpinBox] = {}

        def set_vector_item(property_name: str, index: int, value: float) -> None:
            getattr(component, property_name)[index] = value
            if refresh is not None:
                refresh()

        def commit_val(field: QDoubleSpinBox, property_name: str, index: int) -> None:
            text = field.lineEdit().text().strip()
            if not text:
                field.setValue(float(getattr(field, "original_value", field.value())))
                return
            try:
                new_value = float(text)
            except ValueError:
                field.setValue(float(getattr(field, "original_value", field.value())))
                return
            old_value = float(getattr(field, "original_value", new_value))
            if old_value == new_value:
                return

            def apply(value: float = new_value) -> None:
                getattr(component, property_name)[index] = value
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: float = old_value) -> None:
                getattr(component, property_name)[index] = value
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set Transform.{property_name}_{index}", apply, undo))

        for property_name, label, values in [
            ("position", "Posição", component.position),
            ("rotation", "Rotação", component.rotation),
            ("scale", "Escala", component.scale),
        ]:
            body.addWidget(
                _axis_row(
                    label,
                    values,
                    lambda index, value, prop=property_name: set_vector_item(prop, index, value),
                )
            )
            row = body.itemAt(body.count() - 1).widget()
            spinboxes = row.findChildren(DragScrubSlider)
            for index, field in enumerate(spinboxes):
                fields[(property_name, index)] = field
        widget.sb_pos_x = fields[("position", 0)]
        widget.sb_pos_y = fields[("position", 1)]
        widget.sb_pos_z = fields[("position", 2)]
        widget.sb_rot_x = fields[("rotation", 0)]
        widget.sb_rot_y = fields[("rotation", 1)]
        widget.sb_rot_z = fields[("rotation", 2)]
        widget.sb_sc_x = fields[("scale", 0)]
        widget.sb_sc_y = fields[("scale", 1)]
        widget.sb_sc_z = fields[("scale", 2)]
        widget.commit_val = commit_val
        widget.setProperty("component_type", self.component_type)
        return widget
