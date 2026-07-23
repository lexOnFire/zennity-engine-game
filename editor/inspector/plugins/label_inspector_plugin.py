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


class LabelInspectorPlugin(InspectorPlugin):
    component_type = "Label"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Label")
        text = QLineEdit(str(getattr(component, "text", "")))
        text.editingFinished.connect(lambda: self.set_property(component, "text", text.text(), command_manager, refresh))
        layout.addWidget(_property_row("Text", text))
        font_size = QSpinBox()
        font_size.setRange(1, 200)
        font_size.setValue(int(getattr(component, "font_size", 20)))
        font_size.valueChanged.connect(lambda value: self.set_property(component, "font_size", int(value), command_manager, refresh))
        layout.addWidget(_property_row("Font Size", font_size))
        widget.setProperty("component_type", self.component_type)
        return widget
