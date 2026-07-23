from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QDoubleSpinBox, QHBoxLayout, QLabel, QSpinBox, QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_ui_utils import _property_row, _section
from editor.runtime.command_manager import CommandManager


class CameraInspectorPlugin(InspectorPlugin):
    component_type = "Camera"
    title = "Camera"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Camera")
        layout.addWidget(_property_row(
            "Enabled", _boolean_field(
                self, component, "enabled", command_manager, refresh
            ),
        ))
        layout.addWidget(_property_row(
            "Active", _boolean_field(
                self, component, "active", command_manager, refresh
            ),
        ))
        layout.addWidget(_property_row(
            "Zoom", _number_field(
                self, component, "zoom", 0.01, 100.0, command_manager, refresh
            ),
        ))
        layout.addWidget(_property_row(
            "Priority", _integer_field(
                self, component, "priority", command_manager, refresh
            ),
        ))
        layout.addWidget(_property_row(
            "Clear Color", _color_field(
                self, component, command_manager, refresh
            ),
        ))
        layout.addWidget(_property_row(
            "Viewport Rect", _viewport_field(
                self, component, command_manager, refresh
            ),
        ))
        widget.setProperty("component_type", self.component_type)
        return widget


def _boolean_field(
    plugin: CameraInspectorPlugin, component: Any, attribute: str,
    commands: CommandManager | None, refresh: callable | None,
) -> QCheckBox:
    field = QCheckBox(attribute.title())
    field.setChecked(bool(getattr(component, attribute)))
    field.clicked.connect(
        lambda: plugin.set_property(
            component, attribute, field.isChecked(), commands, refresh
        )
    )
    return field


def _number_field(
    plugin: CameraInspectorPlugin, component: Any, attribute: str,
    minimum: float, maximum: float, commands: CommandManager | None,
    refresh: callable | None,
) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setButtonSymbols(QDoubleSpinBox.NoButtons)
    field.setRange(minimum, maximum)
    field.setSingleStep(0.1)
    field.setValue(float(getattr(component, attribute)))
    field.valueChanged.connect(
        lambda value: plugin.set_property(
            component, attribute, float(value), commands, refresh
        )
    )
    return field


def _integer_field(
    plugin: CameraInspectorPlugin, component: Any, attribute: str,
    commands: CommandManager | None, refresh: callable | None,
) -> QSpinBox:
    field = QSpinBox()
    field.setRange(-999999, 999999)
    field.setValue(int(getattr(component, attribute)))
    field.valueChanged.connect(
        lambda value: plugin.set_property(
            component, attribute, int(value), commands, refresh
        )
    )
    return field


def _color_field(
    plugin: CameraInspectorPlugin, component: Any,
    commands: CommandManager | None, refresh: callable | None,
) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    fields = []
    for label, value in zip("RGB", getattr(component, "clear_color", (30, 30, 30))):
        field = QSpinBox()
        field.setRange(0, 255)
        field.setValue(value)
        fields.append(field)
        layout.addWidget(QLabel(label))
        layout.addWidget(field, 1)

    def update() -> None:
        plugin.set_property(
            component, "clear_color", tuple(field.value() for field in fields),
            commands, refresh,
        )

    for field in fields:
        field.valueChanged.connect(lambda _value: update())
    return row


def _viewport_field(
    plugin: CameraInspectorPlugin, component: Any,
    commands: CommandManager | None, refresh: callable | None,
) -> QWidget:
    row = QWidget()
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    fields = []
    for label, value in zip("XYWH", getattr(component, "viewport_rect", (0.0, 0.0, 1.0, 1.0))):
        field = QDoubleSpinBox()
        field.setButtonSymbols(QDoubleSpinBox.NoButtons)
        field.setRange(0.0, 1.0)
        field.setSingleStep(0.1)
        field.setValue(value)
        fields.append(field)
        layout.addWidget(QLabel(label))
        layout.addWidget(field, 1)

    def update() -> None:
        plugin.set_property(
            component, "viewport_rect", tuple(field.value() for field in fields),
            commands, refresh,
        )

    for field in fields:
        field.valueChanged.connect(lambda _value: update())
    return row
