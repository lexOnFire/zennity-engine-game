from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QCheckBox, QSpinBox, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager
from editor.inspector.plugin_ui_utils import *


class CanvasInspectorPlugin(InspectorPlugin):
    component_type = "Canvas"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Canvas")
        visible = QCheckBox("Visible")
        visible.setChecked(bool(getattr(component, "visible", True)))
        visible.clicked.connect(
            lambda: self.set_property(component, "visible", visible.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Visible", visible))
        z_order = QSpinBox()
        z_order.setRange(-999999, 999999)
        z_order.setValue(int(getattr(component, "z_order", 0)))
        z_order.valueChanged.connect(lambda value: self.set_property(component, "z_order", int(value), command_manager, refresh))
        layout.addWidget(_property_row("Z Order", z_order))
        widget.setProperty("component_type", self.component_type)
        return widget
