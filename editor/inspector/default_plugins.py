from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager


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

        def set_vector_item(property_name: str, index: int, value: float) -> None:
            current = getattr(component, property_name).copy()
            current[index] = value
            self.set_property(component, property_name, current, command_manager, refresh)

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
        for property_name in ("mass", "gravity_scale", "drag"):
            body.addWidget(
                _property_row(
                    property_name,
                    _float_field(
                        getattr(component, property_name),
                        lambda value, prop=property_name: self.set_property(component, prop, value, command_manager, refresh),
                    ),
                )
            )
        for property_name in ("use_gravity", "is_kinematic"):
            field = QCheckBox()
            field.setObjectName("InspectorCheckBox")
            field.setChecked(bool(getattr(component, property_name)))
            field.toggled.connect(
                lambda value, prop=property_name: self.set_property(component, prop, bool(value), command_manager, refresh)
            )
            body.addWidget(_property_row(property_name, field))
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
            body.addWidget(
                _property_row(
                    label,
                    _float_field(
                        getattr(component, property_name),
                        lambda value, prop=property_name: self.set_property(component, prop, value, command_manager, refresh),
                    ),
                )
            )
        for property_name in ("is_trigger", "debug_draw"):
            if hasattr(component, property_name):
                field = QCheckBox()
                field.setObjectName("InspectorCheckBox")
                field.setChecked(bool(getattr(component, property_name)))
                field.toggled.connect(
                    lambda value, prop=property_name: self.set_property(component, prop, bool(value), command_manager, refresh)
                )
                label = "Editar Collider" if property_name == "debug_draw" else "Trigger"
                body.addWidget(_property_row(label, field))
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
        field = QLineEdit(str(getattr(component, "script_path", "")))
        field.setObjectName("InspectorTextField")
        field.editingFinished.connect(
            lambda: self.set_property(component, "script_path", field.text(), command_manager, refresh)
        )
        body.addWidget(_property_row("Script", field))
        widget.setProperty("component_type", self.component_type)
        return widget


def register_default_inspector_plugins() -> None:
    inspector_plugin_registry.register(TransformInspectorPlugin)
    inspector_plugin_registry.register(RigidBodyInspectorPlugin)
    inspector_plugin_registry.register(ColliderInspectorPlugin)
    inspector_plugin_registry.register(ScriptInspectorPlugin)


register_default_inspector_plugins()
