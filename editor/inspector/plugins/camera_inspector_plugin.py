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


class CameraInspectorPlugin(InspectorPlugin):
    component_type = "Camera"
    title = "Camera"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, layout = _section("Camera")

        # enabled
        chk_enabled = QCheckBox("Enabled")
        chk_enabled.setChecked(bool(component.enabled))
        chk_enabled.clicked.connect(
            lambda: self.set_property(component, "enabled", chk_enabled.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Enabled", chk_enabled))

        # active
        chk_active = QCheckBox("Active")
        chk_active.setChecked(bool(component.active))
        chk_active.clicked.connect(
            lambda: self.set_property(component, "active", chk_active.isChecked(), command_manager, refresh)
        )
        layout.addWidget(_property_row("Active", chk_active))

        # zoom
        sb_zoom = QDoubleSpinBox()
        sb_zoom.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_zoom.setRange(0.01, 100.0)
        sb_zoom.setSingleStep(0.1)
        sb_zoom.setValue(float(component.zoom))
        sb_zoom.valueChanged.connect(
            lambda val: self.set_property(component, "zoom", float(val), command_manager, refresh)
        )
        layout.addWidget(_property_row("Zoom", sb_zoom))

        # priority
        sb_priority = QSpinBox()
        sb_priority.setRange(-999999, 999999)
        sb_priority.setValue(int(component.priority))
        sb_priority.valueChanged.connect(
            lambda val: self.set_property(component, "priority", int(val), command_manager, refresh)
        )
        layout.addWidget(_property_row("Priority", sb_priority))

        # clear_color (R, G, B)
        color_row = QWidget()
        color_layout = QHBoxLayout(color_row)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(4)

        current_color = getattr(component, "clear_color", (30, 30, 30))

        sb_r = QSpinBox()
        sb_r.setRange(0, 255)
        sb_r.setValue(current_color[0])
        sb_g = QSpinBox()
        sb_g.setRange(0, 255)
        sb_g.setValue(current_color[1])
        sb_b = QSpinBox()
        sb_b.setRange(0, 255)
        sb_b.setValue(current_color[2])

        def update_color():
            new_color = (sb_r.value(), sb_g.value(), sb_b.value())
            self.set_property(component, "clear_color", new_color, command_manager, refresh)

        sb_r.valueChanged.connect(lambda _: update_color())
        sb_g.valueChanged.connect(lambda _: update_color())
        sb_b.valueChanged.connect(lambda _: update_color())

        color_layout.addWidget(QLabel("R"))
        color_layout.addWidget(sb_r, 1)
        color_layout.addWidget(QLabel("G"))
        color_layout.addWidget(sb_g, 1)
        color_layout.addWidget(QLabel("B"))
        color_layout.addWidget(sb_b, 1)
        layout.addWidget(_property_row("Clear Color", color_row))

        # viewport_rect (X, Y, W, H)
        rect_row = QWidget()
        rect_layout = QHBoxLayout(rect_row)
        rect_layout.setContentsMargins(0, 0, 0, 0)
        rect_layout.setSpacing(4)

        current_rect = getattr(component, "viewport_rect", (0.0, 0.0, 1.0, 1.0))

        sb_x = QDoubleSpinBox()
        sb_x.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_x.setRange(0.0, 1.0)
        sb_x.setSingleStep(0.1)
        sb_x.setValue(current_rect[0])

        sb_y = QDoubleSpinBox()
        sb_y.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_y.setRange(0.0, 1.0)
        sb_y.setSingleStep(0.1)
        sb_y.setValue(current_rect[1])

        sb_w = QDoubleSpinBox()
        sb_w.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_w.setRange(0.0, 1.0)
        sb_w.setSingleStep(0.1)
        sb_w.setValue(current_rect[2])

        sb_h = QDoubleSpinBox()
        sb_h.setButtonSymbols(QDoubleSpinBox.NoButtons)
        sb_h.setRange(0.0, 1.0)
        sb_h.setSingleStep(0.1)
        sb_h.setValue(current_rect[3])

        def update_rect():
            new_rect = (sb_x.value(), sb_y.value(), sb_w.value(), sb_h.value())
            self.set_property(component, "viewport_rect", new_rect, command_manager, refresh)

        sb_x.valueChanged.connect(lambda _: update_rect())
        sb_y.valueChanged.connect(lambda _: update_rect())
        sb_w.valueChanged.connect(lambda _: update_rect())
        sb_h.valueChanged.connect(lambda _: update_rect())

        rect_layout.addWidget(QLabel("X"))
        rect_layout.addWidget(sb_x, 1)
        rect_layout.addWidget(QLabel("Y"))
        rect_layout.addWidget(sb_y, 1)
        rect_layout.addWidget(QLabel("W"))
        rect_layout.addWidget(sb_w, 1)
        rect_layout.addWidget(QLabel("H"))
        rect_layout.addWidget(sb_h, 1)
        layout.addWidget(_property_row("Viewport Rect", rect_row))

        widget.setProperty("component_type", self.component_type)
        return widget
