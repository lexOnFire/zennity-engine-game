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


class AnimatorInspectorPlugin(InspectorPlugin):
    component_type = "Animator"
    title = "Animator"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Animator")

        current_clip = QLineEdit(str(getattr(component, "current_clip", None) or "Nenhum"))
        current_clip.setReadOnly(True)
        layout.addWidget(_property_row("Clip Atual", current_clip))

        playing = QCheckBox("Playing")
        playing.setChecked(bool(getattr(component, "is_any_playing", False)))
        playing.setEnabled(False)
        layout.addWidget(_property_row("Playing", playing))

        loop = QCheckBox("Loop")
        clip_name = getattr(component, "current_clip", None)
        clip = getattr(component, "_clips", {}).get(clip_name) if clip_name else None
        loop.setChecked(bool(getattr(clip, "loop", False)))
        loop.setEnabled(False)
        layout.addWidget(_property_row("Loop", loop))

        speed = QDoubleSpinBox()
        speed.setObjectName("InspectorNumberField")
        speed.setRange(0.0, 100.0)
        speed.setDecimals(2)
        speed.setValue(float(getattr(component, "speed", 1.0)))
        speed.setEnabled(False)
        layout.addWidget(_property_row("Velocidade", speed))

        widget.txt_current_clip = current_clip
        widget.chk_playing = playing
        widget.chk_loop = loop
        widget.sb_speed = speed
        widget.setProperty("component_type", self.component_type)
        return widget
