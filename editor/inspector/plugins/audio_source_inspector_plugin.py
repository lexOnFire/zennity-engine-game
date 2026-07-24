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


class AudioSourceInspectorPlugin(InspectorPlugin):
    component_type = "AudioSource"
    title = "AudioSource"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("AudioSource")

        # enabled
        chk_enabled = QCheckBox("Enabled")
        chk_enabled.setChecked(bool(component.enabled))
        chk_enabled.clicked.connect(
            lambda: self.set_property(component, "enabled", chk_enabled.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Enabled", chk_enabled))

        # audio_clip
        txt_clip = QLineEdit(str(component.audio_clip))
        txt_clip.editingFinished.connect(
            lambda: self.set_property(component, "audio_clip", txt_clip.text(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Audio Clip", txt_clip))

        # volume
        sb_volume = QDoubleSpinBox()
        sb_volume.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_volume.setRange(0.0, 1.0)
        sb_volume.setSingleStep(0.05)
        sb_volume.setValue(float(component.volume))
        sb_volume.valueChanged.connect(
            lambda val: self.set_property(component, "volume", float(val), command_manager, refresh)
        )
        layout.addWidget(_property_row("Volume", sb_volume))

        # pitch
        sb_pitch = QDoubleSpinBox()
        sb_pitch.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_pitch.setRange(0.1, 3.0)
        sb_pitch.setSingleStep(0.05)
        sb_pitch.setValue(float(component.pitch))
        sb_pitch.valueChanged.connect(
            lambda val: self.set_property(component, "pitch", float(val), command_manager, refresh)
        )
        layout.addWidget(_property_row("Pitch", sb_pitch))

        # loop
        chk_loop = QCheckBox("Loop")
        chk_loop.setChecked(bool(component.loop))
        chk_loop.clicked.connect(
            lambda: self.set_property(component, "loop", chk_loop.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Loop", chk_loop))

        # play_on_awake
        chk_awake = QCheckBox("Play on Awake")
        chk_awake.setChecked(bool(component.play_on_awake))
        chk_awake.clicked.connect(
            lambda: self.set_property(component, "play_on_awake", chk_awake.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Play on Awake", chk_awake))

        # mute
        chk_mute = QCheckBox("Mute")
        chk_mute.setChecked(bool(component.mute))
        chk_mute.clicked.connect(
            lambda: self.set_property(component, "mute", chk_mute.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Mute", chk_mute))

        widget.setProperty("component_type", self.component_type)
        return widget
