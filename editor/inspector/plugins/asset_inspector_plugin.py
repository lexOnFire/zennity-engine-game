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


class AssetInspectorPlugin(InspectorPlugin):
    component_type = "AssetInfo" # We map this pseudo-component name for the asset inspector

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Asset Import Settings")

        layout.addWidget(_property_row("UUID", QLabel(getattr(component, "uuid", ""))))
        layout.addWidget(_property_row("Name", QLabel(getattr(component, "name", ""))))
        layout.addWidget(_property_row("Path", QLabel(getattr(component, "path", ""))))
        layout.addWidget(_property_row("Type", QLabel(str(getattr(component, "type", "")))))

        # Read the meta file if possible
        try:
            import json
            meta_path = getattr(component, "metadata_path", None)
            if meta_path and meta_path.exists():
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                importer = data.get("importer", "unknown")
                layout.addWidget(_property_row("Importer", QLabel(importer)))

                settings = data.get("import_settings", {})
                if settings:
                    layout.addWidget(QLabel("Settings:"))
                    for k, v in settings.items():
                        layout.addWidget(_property_row(f"  {k}", QLabel(str(v))))

                deps = data.get("dependencies", [])
                if deps:
                    layout.addWidget(QLabel("Dependencies:"))
                    for d in deps:
                        layout.addWidget(QLabel(f"  - {d}"))
        except Exception:
            layout.addWidget(QLabel("Error reading .meta file."))

        widget.setProperty("component_type", self.component_type)
        return widget
