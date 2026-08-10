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

        choices = getattr(component, "BODY_TYPES", ("dynamic", "kinematic", "static"))
        current_body_type = getattr(component, "body_type", "dynamic")

        def apply_body_type(value: str) -> None:
            setattr(component, "body_type", value)
            if refresh is not None:
                refresh()

        body_type_combo = _enum_field(
            current_body_type,
            choices,
            lambda new_val: self._commit_enum_change(
                component, "body_type", body_type_combo, new_val, command_manager, refresh
            ),
        )
        body.addWidget(_property_row("body_type", body_type_combo))
        widget.combo_body_type = body_type_combo

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

        chk_grav = QCheckBox()
        chk_grav.setObjectName("InspectorCheckBox")
        chk_grav.setChecked(bool(getattr(component, "use_gravity", True)))
        chk_grav.toggled.connect(
            lambda value: self._commit_bool_change(
                component, "use_gravity", chk_grav, bool(value), command_manager, refresh
            )
        )
        body.addWidget(_property_row("use_gravity", chk_grav))
        widget.chk_grav = chk_grav

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

        widget.sb_mass = fields["mass"]
        widget.sb_grav = fields["gravity_scale"]
        widget.commit_val = commit_val
        widget.setProperty("component_type", self.component_type)
        return widget

    def _commit_enum_change(
        self,
        component: Any,
        property_name: str,
        combo: QComboBox,
        new_value: str,
        command_manager: CommandManager | None,
        refresh: callable | None,
    ) -> None:
        old_value = getattr(combo, "original_value", getattr(component, property_name))
        if old_value == new_value:
            return

        def apply(val: str = new_value) -> None:
            setattr(component, property_name, val)
            combo.blockSignals(True)
            for idx in range(combo.count()):
                if combo.itemData(idx) == val:
                    combo.setCurrentIndex(idx)
                    break
            combo.original_value = val
            combo.blockSignals(False)
            if refresh is not None:
                refresh()

        def undo(val: str = old_value) -> None:
            setattr(component, property_name, val)
            combo.blockSignals(True)
            for idx in range(combo.count()):
                if combo.itemData(idx) == val:
                    combo.setCurrentIndex(idx)
                    break
            combo.original_value = val
            combo.blockSignals(False)
            if refresh is not None:
                refresh()

        if command_manager is None:
            apply()
        else:
            command_manager.execute(FunctionCommand(f"Set RigidBody.{property_name}", apply, undo))

    def _commit_bool_change(
        self,
        component: Any,
        property_name: str,
        chk: QCheckBox,
        new_value: bool,
        command_manager: CommandManager | None,
        refresh: callable | None,
    ) -> None:
        old_value = not new_value

        def apply(val: bool = new_value) -> None:
            setattr(component, property_name, val)
            chk.blockSignals(True)
            chk.setChecked(val)
            chk.blockSignals(False)
            if refresh is not None:
                refresh()

        def undo(val: bool = old_value) -> None:
            setattr(component, property_name, val)
            chk.blockSignals(True)
            chk.setChecked(val)
            chk.blockSignals(False)
            if refresh is not None:
                refresh()

        if command_manager is None:
            apply()
        else:
            command_manager.execute(FunctionCommand(f"Set RigidBody.{property_name}", apply, undo))
