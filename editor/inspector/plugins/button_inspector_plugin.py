from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QCheckBox, QLineEdit, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager
from editor.inspector.plugin_ui_utils import *


class ButtonInspectorPlugin(InspectorPlugin):
    component_type = "Button"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Button")
        text = QLineEdit(str(getattr(component, "text", "")))
        text.editingFinished.connect(lambda: self.set_property(component, "text", text.text(), command_manager, refresh))
        layout.addWidget(_property_row("Text", text))
        interactable = QCheckBox("Interactable")
        interactable.setChecked(bool(getattr(component, "interactable", True)))
        interactable.clicked.connect(
            lambda: self.set_property(component, "interactable", interactable.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Interactable", interactable))
        widget.setProperty("component_type", self.component_type)
        return widget
