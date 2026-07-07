from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox

from editor.inspector.default_plugins import _property_row, _section
from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager

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


class InfiniteBackgroundInspectorPlugin(InspectorPlugin):
    component_type = "InfiniteBackground"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ):
        widget, layout = _section("Infinite Background")

        def set_value(prop: str, value: Any) -> None:
            old_value = getattr(component, prop, None)
            if old_value == value:
                return

            def apply() -> None:
                setattr(component, prop, value)
                if refresh is not None:
                    refresh()

            def undo() -> None:
                setattr(component, prop, old_value)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(CommandManager.FunctionCommand(f"Set InfiniteBackground.{prop}", apply, undo))

        # Evita depender da classe interna FunctionCommand quando testes carregam parcial.
        def set_direct(prop: str, value: Any) -> None:
            setattr(component, prop, value)
            if refresh is not None:
                refresh()

        sprite_selector = QComboBox()
        sprite_selector.setObjectName("InspectorInfiniteBackgroundSprite")
        sprite_selector.setEditable(False)
        current = str(getattr(component, "sprite_path", "") or "")
        sprite_selector.addItem("Nenhum")
        paths = _available_sprite_paths()
        if current and current not in paths:
            paths.insert(0, current)
        for path in paths:
            sprite_selector.addItem(path)
        sprite_selector.setCurrentText(current or "Nenhum")
        sprite_selector.activated.connect(
            lambda index: set_direct("sprite_path", "" if sprite_selector.itemText(index) == "Nenhum" else sprite_selector.itemText(index))
        )
        layout.addWidget(_property_row("Sprite", sprite_selector))

        direction = QComboBox()
        direction.setObjectName("InspectorInfiniteBackgroundDirection")
        direction.addItems(["horizontal", "vertical", "both"])
        direction.setCurrentText(str(getattr(component, "direction", "horizontal") or "horizontal"))
        direction.activated.connect(lambda index: set_direct("direction", direction.itemText(index)))
        layout.addWidget(_property_row("Direção", direction))

        def number(prop: str, label: str, value: float, minimum: float = -99999.0, maximum: float = 99999.0, step: float = 1.0):
            field = QDoubleSpinBox()
            field.setObjectName("InspectorNumberField")
            field.setRange(minimum, maximum)
            field.setDecimals(2)
            field.setSingleStep(step)
            field.setValue(float(value))
            field.valueChanged.connect(lambda next_value: set_direct(prop, float(next_value)))
            layout.addWidget(_property_row(label, field))
            return field

        speed_x = number("speed_x", "Velocidade X", getattr(component, "speed_x", 40.0), step=5.0)
        speed_y = number("speed_y", "Velocidade Z/Y", getattr(component, "speed_y", 0.0), step=5.0)
        parallax = number("parallax", "Parallax", getattr(component, "parallax", 0.0), minimum=0.0, maximum=5.0, step=0.1)
        tile_scale = number("tile_scale", "Tile Scale", getattr(component, "tile_scale", 1.0), minimum=0.01, maximum=20.0, step=0.1)
        alpha = number("alpha", "Alpha", getattr(component, "alpha", 255), minimum=0.0, maximum=255.0, step=1.0)

        visible = QCheckBox("Visível")
        visible.setObjectName("InspectorCheckBox")
        visible.setChecked(bool(getattr(component, "visible", True)))
        visible.toggled.connect(lambda checked: set_direct("visible", bool(checked)))
        layout.addWidget(_property_row("Enabled", visible))

        scale_to_screen = QCheckBox("Preencher tela")
        scale_to_screen.setObjectName("InspectorCheckBox")
        scale_to_screen.setChecked(bool(getattr(component, "scale_to_screen", True)))
        scale_to_screen.toggled.connect(lambda checked: set_direct("scale_to_screen", bool(checked)))
        layout.addWidget(_property_row("Scale", scale_to_screen))

        widget.cb_sprite = sprite_selector
        widget.cb_direction = direction
        widget.sb_speed_x = speed_x
        widget.sb_speed_y = speed_y
        widget.sb_parallax = parallax
        widget.sb_tile_scale = tile_scale
        widget.sb_alpha = alpha
        widget.chk_visible = visible
        widget.chk_scale_to_screen = scale_to_screen
        widget.setProperty("component_type", self.component_type)
        return widget


def register_infinite_background_plugin() -> None:
    inspector_plugin_registry.register(InfiniteBackgroundInspectorPlugin)


register_infinite_background_plugin()
