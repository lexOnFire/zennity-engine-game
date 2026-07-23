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


class ImageInspectorPlugin(InspectorPlugin):
    component_type = "Image"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Image")
        sprite_path = QLineEdit(str(getattr(component, "sprite_path", "")))
        sprite_path.editingFinished.connect(
            lambda: self.set_property(component, "sprite_path", sprite_path.text(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Sprite", sprite_path))
        alpha = QSpinBox()
        alpha.setRange(0, 255)
        alpha.setValue(int(getattr(component, "alpha", 255)))
        alpha.valueChanged.connect(lambda value: self.set_property(component, "alpha", int(value), command_manager, refresh))
        layout.addWidget(_property_row("Alpha", alpha))
        widget.setProperty("component_type", self.component_type)
        return widget
