from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from editor.inspector.plugin import InspectorPlugin
from editor.inspector.plugin_registry import inspector_plugin_registry
from editor.runtime.command_manager import CommandManager, FunctionCommand


def _section(title: str) -> tuple[QWidget, QVBoxLayout]:
    widget = QWidget()
    widget.setObjectName("InspectorComponentCard")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header_host = QWidget()
    header_host.setObjectName("InspectorComponentHeader")
    header_layout = QHBoxLayout(header_host)
    header_layout.setContentsMargins(6, 4, 6, 4)
    header_layout.setSpacing(6)

    foldout = QLabel("▾")
    foldout.setObjectName("InspectorFoldout")
    icon = QLabel("✦")
    icon.setObjectName("InspectorComponentIcon")
    header = QLabel(title)
    header.setObjectName("InspectorComponentTitle")
    header_layout.addWidget(foldout)
    header_layout.addWidget(icon)
    header_layout.addWidget(header, 1)
    header_layout.addWidget(QLabel("↻"))
    header_layout.addWidget(QLabel("⋮"))

    body = QWidget()
    body.setObjectName("InspectorComponentBody")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(8, 6, 8, 8)
    body_layout.setSpacing(4)
    layout.addWidget(header_host)
    layout.addWidget(body)
    return widget, body_layout


def _float_field(value: float, on_change: callable) -> QDoubleSpinBox:
    field = QDoubleSpinBox()
    field.setObjectName("InspectorNumberField")
    field.setRange(-999999.0, 999999.0)
    field.setDecimals(2)
    field.setSingleStep(0.1)
    field.setValue(float(value))
    field.valueChanged.connect(lambda next_value: on_change(float(next_value)))
    field.original_value = float(value)
    return field


def _axis_row(label: str, values: Any, on_change: callable) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    for index, axis in enumerate(("X", "Y", "Z")):
        axis_label = QLabel(axis)
        axis_label.setObjectName("InspectorAxisLabel")
        layout.addWidget(axis_label)
        layout.addWidget(_float_field(values[index], lambda value, idx=index: on_change(idx, value)), 1)
    return row


def _property_row(label: str, editor: QWidget) -> QWidget:
    row = QWidget()
    row.setObjectName("InspectorPropertyRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    title = QLabel(label)
    title.setObjectName("InspectorPropertyLabel")
    layout.addWidget(title)
    layout.addWidget(editor, 1)
    return row


def _project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _available_script_paths() -> list[str]:
    scripts_root = Path.cwd() / "Assets" / "Scripts"
    if not scripts_root.exists():
        return []
    return [
        _project_relative(path)
        for path in sorted(scripts_root.rglob("*.py"), key=lambda item: item.as_posix().lower())
        if not path.name.endswith(".meta")
    ]


def _script_template(class_name: str) -> str:
    return (
        "from engine.runtime import Input, ScriptBehaviour\n\n\n"
        f"class {class_name}(ScriptBehaviour):\n"
        "    def on_start(self):\n"
        "        pass\n\n"
        "    def on_update(self, delta_time):\n"
        "        if Input.is_key_down(\"Space\"):\n"
        "            self.transform.position[0] += 120.0 * delta_time\n\n"
        "    def on_destroy(self):\n"
        "        pass\n"
    )


def _safe_script_name(name: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
    return cleaned or "game_object"


def _safe_class_name(name: str) -> str:
    parts = [part for part in _safe_script_name(name).split("_") if part]
    return "".join(part.capitalize() for part in parts) + "Behaviour"


class TransformInspectorPlugin(InspectorPlugin):
    component_type = "Transform"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, body = _section("Transform")
        fields: dict[tuple[str, int], QDoubleSpinBox] = {}

        def set_vector_item(property_name: str, index: int, value: float) -> None:
            getattr(component, property_name)[index] = value
            if refresh is not None:
                refresh()

        def commit_val(field: QDoubleSpinBox, property_name: str, index: int) -> None:
            text = field.lineEdit().text().strip()
            if not text:
                field.setValue(float(getattr(field, "original_value", field.value())))
                return
            try:
                new_value = float(text)
            except ValueError:
                field.setValue(float(getattr(field, "original_value", field.value())))
                return
            old_value = float(getattr(field, "original_value", new_value))
            if old_value == new_value:
                return

            def apply(value: float = new_value) -> None:
                getattr(component, property_name)[index] = value
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: float = old_value) -> None:
                getattr(component, property_name)[index] = value
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set Transform.{property_name}_{index}", apply, undo))

        for property_name, label, values in [
            ("position", "Posição", component.position),
            ("rotation", "Rotação", component.rotation),
            ("scale", "Escala", component.scale),
        ]:
            body.addWidget(
                _axis_row(
                    label,
                    values,
                    lambda index, value, prop=property_name: set_vector_item(prop, index, value),
                )
            )
            row = body.itemAt(body.count() - 1).widget()
            spinboxes = row.findChildren(QDoubleSpinBox)
            for index, field in enumerate(spinboxes):
                fields[(property_name, index)] = field
        widget.sb_pos_x = fields[("position", 0)]
        widget.sb_pos_y = fields[("position", 1)]
        widget.sb_pos_z = fields[("position", 2)]
        widget.sb_rot_x = fields[("rotation", 0)]
        widget.sb_rot_y = fields[("rotation", 1)]
        widget.sb_rot_z = fields[("rotation", 2)]
        widget.sb_sc_x = fields[("scale", 0)]
        widget.sb_sc_y = fields[("scale", 1)]
        widget.sb_sc_z = fields[("scale", 2)]
        widget.commit_val = commit_val
        widget.setProperty("component_type", self.component_type)
        return widget


class RigidBodyInspectorPlugin(InspectorPlugin):
    component_type = "RigidBody"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        widget, body = _section("Rigidbody")
        fields: dict[str, QDoubleSpinBox] = {}
        for property_name in ("mass", "gravity_scale", "drag"):
            row = _property_row(
                property_name,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: setattr(component, prop, value),
                ),
            )
            body.addWidget(row)
            fields[property_name] = row.findChild(QDoubleSpinBox)
        for property_name in ("use_gravity", "is_kinematic"):
            field = QCheckBox()
            field.setObjectName("InspectorCheckBox")
            field.setChecked(bool(getattr(component, property_name)))
            field.toggled.connect(lambda value, prop=property_name: setattr(component, prop, bool(value)))
            body.addWidget(_property_row(property_name, field))
            if property_name == "is_kinematic":
                widget.chk_kin = field

        def commit_val(field: QDoubleSpinBox, property_name: str) -> None:
            old_value = float(getattr(field, "original_value", getattr(component, property_name)))
            text = field.lineEdit().text().strip()
            try:
                new_value = float(text) if text else float(field.value())
            except ValueError:
                field.setValue(old_value)
                return
            if old_value == new_value:
                return

            def apply(value: float = new_value) -> None:
                setattr(component, property_name, value)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: float = old_value) -> None:
                setattr(component, property_name, value)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set RigidBody.{property_name}", apply, undo))

        def commit_kinematic() -> None:
            old_value = not bool(widget.chk_kin.isChecked())
            new_value = bool(widget.chk_kin.isChecked())
            if old_value == new_value:
                return

            def apply(value: bool = new_value) -> None:
                component.is_kinematic = value
                widget.chk_kin.blockSignals(True)
                widget.chk_kin.setChecked(value)
                widget.chk_kin.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: bool = old_value) -> None:
                component.is_kinematic = value
                widget.chk_kin.blockSignals(True)
                widget.chk_kin.setChecked(value)
                widget.chk_kin.blockSignals(False)
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand("Set RigidBody.is_kinematic", apply, undo))

        widget.sb_mass = fields["mass"]
        widget.sb_grav = fields["gravity_scale"]
        widget.commit_val = commit_val
        widget.commit_kinematic = commit_kinematic
        widget.setProperty("component_type", self.component_type)
        return widget


class ColliderInspectorPlugin(InspectorPlugin):
    component_type = "Collider"

    def supports(self, component: Any) -> bool:
        return getattr(component, "type_name", type(component).__name__) in {"BoxCollider", "CircleCollider"}

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        type_name = getattr(component, "type_name", type(component).__name__)
        title = "Box Collider" if type_name == "BoxCollider" else "Circle Collider"
        widget, body = _section(title)
        numeric_fields = ["offset_x", "offset_y"]
        fields: dict[str, QDoubleSpinBox] = {}
        for candidate in ("width", "height", "radius"):
            if hasattr(component, candidate):
                numeric_fields.insert(0, candidate)
        for property_name in numeric_fields:
            label = {
                "offset_x": "Centro X",
                "offset_y": "Centro Y",
                "width": "Tamanho X",
                "height": "Tamanho Y",
                "radius": "Raio",
            }.get(property_name, property_name)
            row = _property_row(
                label,
                _float_field(
                    getattr(component, property_name),
                    lambda value, prop=property_name: setattr(component, prop, value),
                ),
            )
            body.addWidget(row)
            fields[property_name] = row.findChild(QDoubleSpinBox)
        for property_name in ("is_trigger", "debug_draw"):
            if hasattr(component, property_name):
                field = QCheckBox()
                field.setObjectName("InspectorCheckBox")
                field.setChecked(bool(getattr(component, property_name)))
                field.toggled.connect(lambda value, prop=property_name: setattr(component, prop, bool(value)))
                label = "Editar Collider" if property_name == "debug_draw" else "Trigger"
                body.addWidget(_property_row(label, field))
                if property_name == "is_trigger":
                    widget.chk_trigger = field
        if "width" in fields:
            widget.sb_w = fields["width"]
        if "height" in fields:
            widget.sb_h = fields["height"]
        if "radius" in fields:
            widget.sb_r = fields["radius"]

        def commit_val(field: QDoubleSpinBox, property_name: str) -> None:
            old_value = int(getattr(field, "original_value", getattr(component, property_name)))
            new_value = int(field.value())
            if old_value == new_value:
                return
            owner = getattr(component, "game_object", None)

            def apply(value: int = new_value) -> None:
                setattr(component, property_name, value)
                if owner is not None:
                    if property_name == "width":
                        owner.transform.scale[0] = float(value)
                    elif property_name == "height":
                        owner.transform.scale[1] = float(value)
                    elif property_name == "radius":
                        owner.transform.scale[0] = float(value * 2)
                        owner.transform.scale[1] = float(value * 2)
                field.blockSignals(True)
                field.setValue(value)
                field.original_value = value
                field.blockSignals(False)
                if refresh is not None:
                    refresh()

            def undo(value: int = old_value) -> None:
                apply(value)

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand(f"Set Collider.{property_name}", apply, undo))

        widget.commit_val = commit_val
        widget.setProperty("component_type", type_name)
        return widget


class ScriptInspectorPlugin(InspectorPlugin):
    component_type = "Script"

    def create_widget(
        self,
        component: Any,
        command_manager: CommandManager | None,
        refresh: callable | None = None,
    ) -> QWidget:
        owner_name = getattr(getattr(component, "game_object", None), "name", "Player")
        widget, body = _section(f"{owner_name} (Script)")
        field = QComboBox()
        field.setObjectName("InspectorTextField")
        field.setEditable(True)

        def refresh_scripts_list() -> None:
            current = str(getattr(component, "script_path", "") or "")
            field.blockSignals(True)
            field.clear()
            field.addItem("Nenhum")
            paths = _available_script_paths()
            if current and current not in paths:
                paths.insert(0, current)
            for path in paths:
                field.addItem(path)
            field.setCurrentText(current or "Nenhum")
            field.blockSignals(False)

        edit_button = QPushButton("Editar")
        edit_button.setObjectName("InspectorScriptEditButton")
        create_button = QPushButton("Criar")
        create_button.setObjectName("InspectorScriptCreateButton")

        buttons = QWidget()
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(create_button)

        refresh_scripts_list()
        edit_button.setEnabled(bool(getattr(component, "script_path", "")))
        body.addWidget(_property_row("Script", field))
        body.addWidget(_property_row("", buttons))

        def set_script_path(new_value: str) -> None:
            old_value = str(getattr(component, "script_path", ""))
            if new_value == "Nenhum":
                new_value = ""
            if old_value == new_value:
                return

            def apply(value: str = new_value) -> None:
                component.script_path = value
                refresh_scripts_list()
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            def undo(value: str = old_value) -> None:
                component.script_path = value
                refresh_scripts_list()
                edit_button.setEnabled(bool(value))
                if refresh is not None:
                    refresh()

            if command_manager is None:
                apply()
            else:
                command_manager.execute(FunctionCommand("Set Script.script_path", apply, undo))

        def on_script_activated(index: int) -> None:
            new_value = field.itemText(index) if index >= 0 else field.currentText()
            set_script_path(new_value)

        def edit_current_script() -> None:
            script_path = str(getattr(component, "script_path", "") or "").strip()
            if not script_path:
                return
            path = Path(script_path)
            if not path.is_absolute():
                path = Path.cwd() / path
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

        def create_script() -> None:
            owner = getattr(component, "game_object", None)
            name = getattr(owner, "name", owner_name)
            scripts_root = Path.cwd() / "Assets" / "Scripts"
            scripts_root.mkdir(parents=True, exist_ok=True)
            base = _safe_script_name(str(name))
            path = scripts_root / f"{base}.py"
            suffix = 1
            while path.exists():
                path = scripts_root / f"{base}_{suffix}.py"
                suffix += 1
            path.write_text(_script_template(_safe_class_name(str(name))), encoding="utf-8")
            set_script_path(_project_relative(path))

        field.activated.connect(on_script_activated)
        edit_button.clicked.connect(edit_current_script)
        create_button.clicked.connect(create_script)
        widget.cb_scripts = field
        widget.btn_edit = edit_button
        widget.btn_create = create_button
        widget.refresh_scripts_list = refresh_scripts_list
        widget.on_script_activated = on_script_activated
        widget.create_script = create_script
        widget.setProperty("component_type", self.component_type)
        return widget


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
        sb_x.setRange(0.0, 1.0)
        sb_x.setSingleStep(0.1)
        sb_x.setValue(current_rect[0])
        
        sb_y = QDoubleSpinBox()
        sb_y.setRange(0.0, 1.0)
        sb_y.setSingleStep(0.1)
        sb_y.setValue(current_rect[1])
        
        sb_w = QDoubleSpinBox()
        sb_w.setRange(0.0, 1.0)
        sb_w.setSingleStep(0.1)
        sb_w.setValue(current_rect[2])
        
        sb_h = QDoubleSpinBox()
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
        sb_volume.setRange(0.0, 1.0)
        sb_volume.setSingleStep(0.05)
        sb_volume.setValue(float(component.volume))
        sb_volume.valueChanged.connect(
            lambda val: self.set_property(component, "volume", float(val), command_manager, refresh)
        )
        layout.addWidget(_property_row("Volume", sb_volume))

        # pitch
        sb_pitch = QDoubleSpinBox()
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


def register_default_inspector_plugins() -> None:
    inspector_plugin_registry.register(TransformInspectorPlugin)
    inspector_plugin_registry.register(RigidBodyInspectorPlugin)
    inspector_plugin_registry.register(ColliderInspectorPlugin)
    inspector_plugin_registry.register(ScriptInspectorPlugin)
    inspector_plugin_registry.register(CameraInspectorPlugin)
    inspector_plugin_registry.register(AudioSourceInspectorPlugin)
    inspector_plugin_registry.register(AudioListenerInspectorPlugin)


register_default_inspector_plugins()
