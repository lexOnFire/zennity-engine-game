from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager


def _section(title: str) -> tuple[QWidget, QFormLayout]:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    header = QLabel(title)
    header.setObjectName("InspectorSection")
    form_host = QWidget()
    form = QFormLayout(form_host)
    form.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(header)
    layout.addWidget(form_host)
    return widget, form


def _float_field(value: float, on_change: callable) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setRange(-999999.0, 999999.0)
    field.setDecimals(3)
    field.setSingleStep(0.1)
    field.setValue(float(value))
    field.valueChanged.connect(lambda next_value: on_change(float(next_value)))
    return field


class TransformInspectorPlugin(InspectorPlugin):
    component_type = "Transform"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, form = _section("Transform")

        def set_vector_item(property_name: str, index: int, value: float) -> None:
            current = getattr(component, property_name).copy()
            current[index] = value
            self.set_property(component, property_name, current, command_manager, refresh)

        for property_name, label, values in [
            ("position", "Position", component.position),
            ("rotation", "Rotation", component.rotation),
            ("scale", "Scale", component.scale),
        ]:
            for index, axis in enumerate(("X", "Y", "Z")):
                form.addRow(
                    f"{label} {axis}",
                    _float_field(values[index], lambda value, prop=property_name, idx=index: set_vector_item(prop, idx, value)),
                )
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
        widget, form = _section("RigidBody")
        for property_name in ("mass", "gravity_scale", "drag"):
            form.addRow(
                property_name,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: self.set_property(component, prop, value, command_manager, refresh),
                ),
            )
        for property_name in ("use_gravity", "is_kinematic"):
            field = QCheckBox()
            field.setChecked(bool(getattr(component, property_name)))
            field.toggled.connect(
                lambda value, prop=property_name: self.set_property(component, prop, bool(value), command_manager, refresh)
            )
            form.addRow(property_name, field)
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
        widget, form = _section(type_name)
        numeric_fields = ["offset_x", "offset_y"]
        for candidate in ("width", "height", "radius"):
            if hasattr(component, candidate):
                numeric_fields.insert(0, candidate)
        for property_name in numeric_fields:
            form.addRow(
                property_name,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: self.set_property(component, prop, value, command_manager, refresh),
                ),
            )
        for property_name in ("is_trigger", "debug_draw"):
            if hasattr(component, property_name):
                field = QCheckBox()
                field.setChecked(bool(getattr(component, property_name)))
                field.toggled.connect(
                    lambda value, prop=property_name: self.set_property(component, prop, bool(value), command_manager, refresh)
                )
                form.addRow(property_name, field)
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
        widget, form = _section("Script")
        field = QLineEdit(str(getattr(component, "script_path", "")))
        field.editingFinished.connect(
            lambda: self.set_property(component, "script_path", field.text(), command_manager, refresh)
        )
        form.addRow("script_path", field)
        widget.setProperty("component_type", self.component_type)
        return widget


def register_default_inspector_plugins() -> None:
    inspector_plugin_registry.register(TransformInspectorPlugin)
    inspector_plugin_registry.register(RigidBodyInspectorPlugin)
    inspector_plugin_registry.register(ColliderInspectorPlugin)
    inspector_plugin_registry.register(ScriptInspectorPlugin)


register_default_inspector_plugins()
