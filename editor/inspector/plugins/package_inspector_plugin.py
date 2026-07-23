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


class PackageInspectorPlugin(InspectorPlugin):
    component_type = "PackageManager"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Package Manager")
        
        try:
            packages = component.registry.list_packages()
            if not packages:
                layout.addWidget(QLabel("No packages installed."))
            else:
                for pkg in packages:
                    layout.addWidget(QLabel(f"<b>{pkg.name}</b> v{pkg.version}"))
                    if pkg.description:
                        layout.addWidget(QLabel(f"  <i>{pkg.description}</i>"))
                    if pkg.author:
                        layout.addWidget(QLabel(f"  Author: {pkg.author}"))
                    layout.addWidget(QLabel("---"))
        except Exception as e:
            layout.addWidget(QLabel(f"Error reading packages: {e}"))
            
        widget.setProperty("component_type", self.component_type)
        return widget


