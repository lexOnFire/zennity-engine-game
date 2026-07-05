from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager, FunctionCommand


def _section(title: str) -> tuple[QWidget, QVBoxLayout]:
    widget = QWidget()
    widget.setObjectName("InspectorComponentCard")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header_host = QWidget()
    header_host.setObjectName("InspectorComponentHeader")
    header_layout = QHBoxLayout(header_host)
    header_layout.setContentsMargins(6, 4, 6, 4)
    header_layout.setSpacing(6)

    foldout = QLabel("▾")
    foldout.setObjectName("InspectorFoldout")
    icon = QLabel("✦")
    icon.setObjectName("InspectorComponentIcon")
    header = QLabel(title)
    header.setObjectName("InspectorComponentTitle")
    header_layout.addWidget(foldout)
    header_layout.addWidget(icon)
    header_layout.addWidget(header, 1)
    header_layout.addWidget(QLabel("↻"))
    header_layout.addWidget(QLabel("⋮"))

    body = QWidget()
    body.setObjectName("InspectorComponentBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(8, 6, 8, 8)
    body_layout.setSpacing(4)
    layout.addWidget(header_host)
    layout.addWidget(body)
    return widget, body_layout


def _float_field(value: float, on_change: callable) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setObjectName("InspectorNumberField")
    field.setRange(-999999.0, 999999.0)
    field.setDecimals(2)
    field.setSingleStep(0.1)
    field.setValue(float(value))
    field.valueChanged.connect(lambda next_value: on_change(float(next_value)))
    field.original_value = float(value)
    return field


def _axis_row(label: str, values: Any, on_change: callable) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    for index, axis in enumerate(("X", "Y", "Z")):
        axis_label = QLabel(axis)
        axis_label.setObjectName("InspectorAxisLabel")
        layout.addWidget(axis_label)
        layout.addWidget(_float_field(values[index], lambda value, idx=index: on_change(idx, value)), 1)
    return row


def _property_row(label: str, editor: QWidget) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    layout.addWidget(editor, 1)
    return row


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
            spinboxes = row.findChildren(QDoubleSpinBox)
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


class ColliderInspectorPlugin(InspectorPlugin):
    component_type = "Collider"

    def supports(self, component: Any) -> bool:
        return getattr(component, "type_name", type(component).__name__) in {"BoxCollider", "CircleCollider"}

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        type_name = getattr(component, "type_name", type(component).__name__)
        title = "Box Collider" if type_name == "BoxCollider" else "Circle Collider"
        widget, body = _section(title)
        numeric_fields = ["offset_x", "offset_y"]
        fields: dict[str, QDoubleSpinBox] = {}
        for candidate in ("width", "height", "radius"):
            if hasattr(component, candidate):
                numeric_fields.insert(0, candidate)
        for property_name in numeric_fields:
            label = {
                "offset_x": "Centro X",
                "offset_y": "Centro Y",
                "width": "Tamanho X",
                "height": "Tamanho Y",
                "radius": "Raio",
            }.get(property_name, property_name)
            row = _property_row(
                label,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: setattr(component, prop, value),
                ),
            )
            body.addWidget(row)
            fields[property_name] = row.findChild(QDoubleSpinBox)
        for property_name in ("is_trigger", "debug_draw"):
            if hasattr(component, property_name):
                field = QCheckBox()
                field.setObjectName("InspectorCheckBox")
                field.setChecked(bool(getattr(component, property_name)))
                field.toggled.connect(lambda value, prop=property_name: setattr(component, prop, bool(value)))
                label = "Editar Collider" if property_name == "debug_draw" else "Trigger"
                body.addWidget(_property_row(label, field))
                if property_name == "is_trigger":
                    widget.chk_trigger = field
        if "width" in fields:
            widget.sb_w = fields["width"]
        if "height" in fields:
            widget.sb_h = fields["height"]
        if "radius" in fields:
            widget.sb_r = fields["radius"]

        def commit_val(field: QDoubleSpinBox, property_name: str) -> None:
            old_value = int(getattr(field, "original_value", getattr(component, property_name)))
            new_value = int(field.value())
            if old_value == new_value:
                return
            owner = getattr(component, "game_object", None)

            def apply(value: int = new_value) -> None:
                setattr(component, property_name, value)
                if owner is not None:
                    if property_name == "width":
                        owner.transform.scale[0] = float(value)
                    elif property_name == "height":
                        owner.transform.scale[1] = float(value)
                    elif property_name == "radius":
                        owner.transform.scale[0] = float(value * 2)
                        owner.transform.scale[1] = float(value * 2)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: int = old_value) -> None:
                apply(value)

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set Collider.{property_name}", apply, undo))

        widget.commit_val = commit_val
        widget.setProperty("component_type", type_name)
        return widget


class ScriptInspectorPlugin(InspectorPlugin):
    component_type = "Script"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        owner_name = getattr(getattr(component, "game_object", None), "name", "Player")
        widget, body = _section(f"{owner_name} (Script)")
        field = QComboBox()
        field.setObjectName("InspectorCombo")
        field.addItem(str(getattr(component, "script_path", "") or "Nenhum"))
        field.setObjectName("InspectorTextField")
        field.setEditable(True)
        edit_button = QCheckBox("Editar")
        edit_button.setEnabled(bool(getattr(component, "script_path", "")))
        body.addWidget(_property_row("Script", field))
        body.addWidget(_property_row("", edit_button))

        def on_script_activated(index: int) -> None:
            old_value = str(getattr(component, "script_path", ""))
            new_value = field.itemText(index) if index >= 0 else field.currentText()
            if new_value == "Nenhum":
                new_value = ""
            if old_value == new_value:
                return

            def apply(value: str = new_value) -> None:
                component.script_path = value
                field.setCurrentText(value or "Nenhum")
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            def undo(value: str = old_value) -> None:
                component.script_path = value
                field.setCurrentText(value or "Nenhum")
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand("Set Script.script_path", apply, undo))

        field.activated.connect(on_script_activated)
        widget.cb_scripts = field
        widget.btn_edit = edit_button
        widget.refresh_scripts_list = lambda: None
        widget.on_script_activated = on_script_activated
        widget.setProperty("component_type", self.component_type)
        return widget


def register_default_inspector_plugins() -> None:
    inspector_plugin_registry.register(TransformInspectorPlugin)
    inspector_plugin_registry.register(RigidBodyInspectorPlugin)
    inspector_plugin_registry.register(ColliderInspectorPlugin)
    inspector_plugin_registry.register(ScriptInspectorPlugin)


register_default_inspector_plugins()
