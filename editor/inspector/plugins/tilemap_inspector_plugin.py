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


class TilemapInspectorPlugin(InspectorPlugin):
    component_type = "Tilemap"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Tilemap")

        # Width
        width_spin = QSpinBox()
        width_spin.setRange(1, 1000)
        width_spin.setValue(int(getattr(component, "width", 10)))
        width_spin.valueChanged.connect(
            lambda: self.set_property(component, "width", width_spin.value(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Width", width_spin))

        # Height
        height_spin = QSpinBox()
        height_spin.setRange(1, 1000)
        height_spin.setValue(int(getattr(component, "height", 10)))
        height_spin.valueChanged.connect(
            lambda: self.set_property(component, "height", height_spin.value(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Height", height_spin))

        # Tile Size
        size_spin = QSpinBox()
        size_spin.setRange(1, 256)
        size_spin.setValue(int(getattr(component, "tile_size", 32)))
        size_spin.valueChanged.connect(
            lambda: self.set_property(component, "tile_size", size_spin.value(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Tile Size", size_spin))

        # Layers info
        layers_count = len(getattr(component, "layers", []))
        layout.addWidget(_property_row("Layers", QLabel(str(layers_count))))

        widget.setProperty("component_type", self.component_type)
        return widget
