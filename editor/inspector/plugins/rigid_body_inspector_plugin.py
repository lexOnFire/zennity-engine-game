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


class RigidBodyInspectorPlugin(InspectorPlugin):
    component_type = "RigidBody"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, body = _section("Rigidbody")
        fields: dict[str, QDoubleSpinBox] = {}
        for property_name in ("mass", "gravity_scale", "drag"):
            row = _property_row(
                property_name,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: setattr(component, prop, value),
                ),
            )
            body.addWidget(row)
            fields[property_name] = row.findChild(QDoubleSpinBox)
        for property_name in ("use_gravity", "is_kinematic"):
            field = QCheckBox()
            field.setObjectName("InspectorCheckBox")
            field.setChecked(bool(getattr(component, property_name)))
            field.toggled.connect(lambda value, prop=property_name: setattr(component, prop, bool(value)))
            body.addWidget(_property_row(property_name, field))
            if property_name == "is_kinematic":
                widget.chk_kin = field

        def commit_val(field: QDoubleSpinBox, property_name: str) -> None:
            old_value = float(getattr(field, "original_value", getattr(component, property_name)))
            text = field.lineEdit().text().strip()
            try:
                new_value = float(text) if text else float(field.value())
            except ValueError:
                field.setValue(old_value)
                return
            if old_value == new_value:
                return

            def apply(value: float = new_value) -> None:
                setattr(component, property_name, value)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: float = old_value) -> None:
                setattr(component, property_name, value)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set RigidBody.{property_name}", apply, undo))

        def commit_kinematic() -> None:
            old_value = not bool(widget.chk_kin.isChecked())
            new_value = bool(widget.chk_kin.isChecked())
            if old_value == new_value:
                return

            def apply(value: bool = new_value) -> None:
                component.is_kinematic = value
                widget.chk_kin.blockSignals(True)
                widget.chk_kin.setChecked(value)
                widget.chk_kin.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: bool = old_value) -> None:
                component.is_kinematic = value
                widget.chk_kin.blockSignals(True)
                widget.chk_kin.setChecked(value)
                widget.chk_kin.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand("Set RigidBody.is_kinematic", apply, undo))

        widget.sb_mass = fields["mass"]
        widget.sb_grav = fields["gravity_scale"]
        widget.commit_val = commit_val
        widget.commit_kinematic = commit_kinematic
        widget.setProperty("component_type", self.component_type)
        return widget
