from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QLabel, QPushButton

from editor.inspector.default_plugins import _property_row, _section
from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager
from editor.runtime.editor2d_sprite_patch import apply_editor2d_sprite_patch


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}


def _project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _available_sprite_paths() -> list[str]:
    roots = [Path.cwd() / "Assets", Path.cwd() / "examples"]
    paths: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in _IMAGE_EXTENSIONS and not path.name.endswith(".meta"):
                paths.append(_project_relative(path))
    return sorted(set(paths), key=str.lower)


class AssetAwareImageInspectorPlugin(InspectorPlugin):
    """Inspector de Image com seletor de sprites encontrados em Assets."""

    component_type = "Image"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ):
        widget, layout = _section("Image")
        sprite_selector = QComboBox()
        sprite_selector.setObjectName("InspectorSpriteSelector")
        sprite_selector.setEditable(False)

        current = str(getattr(component, "sprite_path", "") or "")
        sprite_selector.addItem("Nenhum")
        paths = _available_sprite_paths()
        if current and current not in paths:
            paths.insert(0, current)
        for path in paths:
            sprite_selector.addItem(path)
        sprite_selector.setCurrentText(current or "Nenhum")

        def set_sprite_path(value: str) -> None:
            next_value = "" if value == "Nenhum" else value.strip()
            old_value = str(getattr(component, "sprite_path", "") or "")
            if old_value == next_value:
                return
            self.set_property(component, "sprite_path", next_value, command_manager, refresh)

        sprite_selector.activated.connect(lambda index: set_sprite_path(sprite_selector.itemText(index)))
        layout.addWidget(_property_row("Sprite", sprite_selector))

        alpha = QDoubleSpinBox()
        alpha.setObjectName("InspectorNumberField")
        alpha.setRange(0, 255)
        alpha.setDecimals(0)
        alpha.setValue(float(getattr(component, "alpha", 255)))
        alpha.valueChanged.connect(lambda value: self.set_property(component, "alpha", int(value), command_manager, refresh))
        layout.addWidget(_property_row("Alpha", alpha))

        widget.cb_sprite = sprite_selector
        widget.sb_alpha = alpha
        widget.set_sprite_path = set_sprite_path
        widget.setProperty("component_type", self.component_type)
        return widget


class AssetAwareAnimatorInspectorPlugin(InspectorPlugin):
    """Inspector de Animator com estado útil mesmo sem clips criados."""

    component_type = "Animator"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ):
        widget, layout = _section("Animator")
        clips = sorted(getattr(component, "_clips", {}).keys())

        default_clip = QComboBox()
        default_clip.setObjectName("InspectorAnimatorDefaultClip")
        default_clip.addItem("Nenhum")
        for clip_name in clips:
            default_clip.addItem(clip_name)
        default_clip.setCurrentText(str(getattr(component, "_default", "") or "Nenhum"))
        default_clip.setEnabled(bool(clips))
        default_clip.activated.connect(
            lambda index: self.set_property(
                component,
                "_default",
                None if default_clip.itemText(index) == "Nenhum" else default_clip.itemText(index),
                command_manager,
                refresh,
            )
        )
        layout.addWidget(_property_row("Clip Inicial", default_clip))

        current = QLabel(str(getattr(component, "current_clip", None) or "Nenhum"))
        current.setObjectName("InspectorAnimatorCurrentClip")
        layout.addWidget(_property_row("Clip Atual", current))

        speed = QDoubleSpinBox()
        speed.setObjectName("InspectorNumberField")
        speed.setRange(0.0, 100.0)
        speed.setDecimals(2)
        speed.setSingleStep(0.1)
        speed.setValue(float(getattr(component, "speed", 1.0)))
        speed.valueChanged.connect(lambda value: self.set_property(component, "speed", float(value), command_manager, refresh))
        layout.addWidget(_property_row("Velocidade", speed))

        play_button = QPushButton("Play Clip")
        play_button.setObjectName("InspectorAnimatorPlayButton")
        play_button.setEnabled(bool(clips))
        stop_button = QPushButton("Stop")
        stop_button.setObjectName("InspectorAnimatorStopButton")

        def play_selected() -> None:
            selected = default_clip.currentText()
            if selected and selected != "Nenhum":
                component.play(selected, force=True)
                if refresh is not None:
                    refresh()

        def stop() -> None:
            component.stop()
            if refresh is not None:
                refresh()

        play_button.clicked.connect(play_selected)
        stop_button.clicked.connect(stop)
        layout.addWidget(_property_row("Controles", play_button))
        layout.addWidget(_property_row("", stop_button))

        if not clips:
            hint = QLabel("Nenhum clip criado ainda. Use a futura aba Animator para criar clips e frames.")
            hint.setWordWrap(True)
            hint.setObjectName("InspectorHint")
            layout.addWidget(hint)

        widget.cb_default_clip = default_clip
        widget.lbl_current_clip = current
        widget.sb_speed = speed
        widget.btn_play_clip = play_button
        widget.btn_stop = stop_button
        widget.setProperty("component_type", self.component_type)
        return widget


def register_asset_component_plugins() -> None:
    inspector_plugin_registry.register(AssetAwareImageInspectorPlugin)
    inspector_plugin_registry.register(AssetAwareAnimatorInspectorPlugin)
    apply_editor2d_sprite_patch()


register_asset_component_plugins()
