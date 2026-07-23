from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QLabel, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager
from editor.inspector.plugin_ui_utils import *


class TilemapRendererInspectorPlugin(InspectorPlugin):
    component_type = "TilemapRenderer"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Tilemap Renderer")

        info = QLabel("Requires a Tilemap component on the same GameObject.")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)

        widget.setProperty("component_type", self.component_type)
        return widget
