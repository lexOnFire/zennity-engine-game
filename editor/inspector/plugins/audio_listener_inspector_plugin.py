from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import QCheckBox, QWidget
from editor.inspector.plugin import InspectorPlugin
from editor.runtime.command_manager import CommandManager
from editor.inspector.plugin_ui_utils import *


class AudioListenerInspectorPlugin(InspectorPlugin):
    component_type = "AudioListener"
    title = "AudioListener"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("AudioListener")

        # enabled
        chk_enabled = QCheckBox("Enabled")
        chk_enabled.setChecked(bool(component.enabled))
        chk_enabled.clicked.connect(
            lambda: self.set_property(component, "enabled", chk_enabled.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Enabled", chk_enabled))

        widget.setProperty("component_type", self.component_type)
        return widget
