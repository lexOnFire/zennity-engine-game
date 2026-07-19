"""Inspector signal wiring and card presentation for the isolated editor."""
from __future__ import annotations

from typing import Any
from copy import deepcopy


class IsolatedInspectorController:
    """Own Inspector UI wiring without owning the editor window or scene model."""

    CARD_WIDGETS = {
        "transform": ("transform_header", "transform_body", "btn_collapse_transform"),
        "sprite": ("sprite_renderer_header", "sprite_renderer_body", "btn_collapse_renderer"),
        "audio": ("audio_source_header", "audio_source_body", "btn_collapse_audio"),
        "rigidbody": ("rigidbody_header", "rigidbody_body", "btn_collapse_rigidbody"),
        "collider": ("collider_header", "collider_body", "btn_collapse_collider"),
        "camera": ("camera_header", "camera_body", "btn_collapse_camera"),
        "ui": ("ui_component_header", "ui_component_body", "btn_collapse_ui"),
        "logic": ("logic_component_header", "logic_component_body", "btn_collapse_logic"),
        "runtime": ("runtime_debug_header", "runtime_debug_body", "btn_collapse_runtime"),
    }

    def __init__(self, host: Any) -> None:
        self.host = host
        self._connected = False

    def connect(self) -> bool:
        """Connect all Inspector signals once and report whether wiring occurred."""
        if self._connected:
            return False
        h = self.host
        for field in h.inspector_fields.values():
            field.valueChanged.connect(lambda _value: h._send_inspector_transform())
        for field in h.physics_fields.values():
            field.toggled.connect(lambda _checked: h._send_inspector_physics())
        for field in h.collider_fields.values():
            field.valueChanged.connect(lambda _value: h._send_inspector_collider())
        h.collider_trigger_field.toggled.connect(lambda _checked: h._send_inspector_collider())

        h.show_rigidbody_chk.toggled.connect(h._toggle_rigidbody_component)
        h.show_collider_chk.toggled.connect(h._toggle_collider_component)
        h.show_animator_chk.toggled.connect(h._toggle_animator_component)
        h.btn_del_rb.clicked.connect(lambda: h.show_rigidbody_chk.setChecked(False))
        h.btn_del_col.clicked.connect(lambda: h.show_collider_chk.setChecked(False))
        h.btn_del_anim.clicked.connect(lambda: h.show_animator_chk.setChecked(False))
        h.show_renderer_chk.toggled.connect(h._toggle_renderer_component)
        h.sprite_texture_button.clicked.connect(h._choose_sprite_texture)
        h.sprite_color_button.clicked.connect(h._choose_sprite_color)
        h.sprite_layer_combo.currentTextChanged.connect(lambda _text: h._send_inspector_renderer())
        h.sprite_order_field.valueChanged.connect(lambda _value: h._send_inspector_renderer())
        h.btn_collapse_transform.clicked.connect(lambda: h._toggle_inspector_card("transform"))
        h.btn_collapse_renderer.clicked.connect(lambda: h._toggle_inspector_card("sprite"))
        h.btn_delete_renderer.clicked.connect(lambda: h.show_renderer_chk.setChecked(False))
        h.show_audio_chk.toggled.connect(h._toggle_audio_component)
        h.btn_collapse_audio.clicked.connect(lambda: h._toggle_inspector_card("audio"))
        h.btn_delete_audio.clicked.connect(lambda: h.show_audio_chk.setChecked(False))
        h.audio_path_combo.activated.connect(lambda _idx: h._send_inspector_audio())
        h.audio_volume_field.valueChanged.connect(lambda _value: h._send_inspector_audio())
        h.audio_loop_field.toggled.connect(lambda _value: h._send_inspector_audio())
        h.audio_autoplay_field.toggled.connect(lambda _value: h._send_inspector_audio())
        h.audio_test_button.clicked.connect(h._test_selected_audio)
        h.audio_stop_button.clicked.connect(lambda: h._commands.put({"type": "stop_audio_preview"}))
        h.animator_clip_combo.currentTextChanged.connect(lambda _text: h._send_inspector_animator())
        h.animator_speed_field.valueChanged.connect(lambda _value: h._send_inspector_animator())
        h.animator_sheet_combo.currentIndexChanged.connect(lambda _value: h._send_inspector_animator())
        for field in (
            h.animator_frame_width, h.animator_frame_height, h.animator_start_frame,
            h.animator_frame_count, h.animator_fps_field,
        ):
            field.valueChanged.connect(lambda _value: h._send_inspector_animator())
        h.animator_loop_field.toggled.connect(lambda _value: h._send_inspector_animator())
        h.animator_add_clip_button.clicked.connect(h._add_animation_clip)
        h.animator_remove_clip_button.clicked.connect(h._remove_animation_clip)
        h.show_camera_chk.toggled.connect(h._toggle_camera_component)
        h.btn_collapse_rigidbody.clicked.connect(lambda: h._toggle_inspector_card("rigidbody"))
        h.btn_collapse_collider.clicked.connect(lambda: h._toggle_inspector_card("collider"))
        h.btn_collapse_camera.clicked.connect(lambda: h._toggle_inspector_card("camera"))
        h.btn_delete_camera.clicked.connect(lambda: h.show_camera_chk.setChecked(False))
        h.camera_active_field.toggled.connect(lambda _value: h._send_inspector_camera())
        h.camera_width_field.valueChanged.connect(lambda _value: h._send_inspector_camera())
        h.camera_height_field.valueChanged.connect(lambda _value: h._send_inspector_camera())
        h.camera_zoom_field.valueChanged.connect(lambda _value: h._send_inspector_camera())
        h.camera_follow_combo.currentTextChanged.connect(lambda _value: h._send_inspector_camera())
        h.camera_color_button.clicked.connect(h._choose_camera_color)
        h.show_ui_chk.toggled.connect(h._toggle_ui_visibility)
        h.btn_collapse_ui.clicked.connect(lambda: h._toggle_inspector_card("ui"))
        h.btn_delete_ui.clicked.connect(h._delete_ui_component)
        h.ui_text_field.editingFinished.connect(h._send_inspector_ui)
        for field in h.ui_position_fields.values():
            field.valueChanged.connect(lambda _value: h._send_inspector_ui())
        h.ui_color_button.clicked.connect(h._choose_ui_color)
        h.ui_image_button.clicked.connect(h._choose_ui_image)
        h.ui_interactable_field.toggled.connect(lambda _value: h._send_inspector_ui())
        h.ui_event_field.editingFinished.connect(h._send_inspector_ui)
        h.ui_target_combo.currentTextChanged.connect(lambda _value: h._send_inspector_ui())
        h.btn_collapse_logic.clicked.connect(lambda: h._toggle_inspector_card("logic"))
        h.btn_collapse_runtime.clicked.connect(lambda: h._toggle_inspector_card("runtime"))
        h.btn_delete_logic.clicked.connect(h._remove_all_logic_graphs)
        h.logic_graph_combo.currentIndexChanged.connect(h._update_logic_graph_summary)
        h.logic_open_button.clicked.connect(h._open_selected_logic_graph)
        h.logic_link_button.clicked.connect(h._choose_logic_graph_component)
        h.logic_new_button.clicked.connect(h._create_logic_graph_for_selected)
        h.logic_unlink_button.clicked.connect(h._detach_selected_logic_graph)
        self._connected = True
        return True

    def card(self, key: str) -> tuple[Any, Any, Any]:
        attributes = self.CARD_WIDGETS[key]
        return tuple(getattr(self.host, name) for name in attributes)

    def set_card_present(self, key: str, present: bool) -> None:
        header, body, button = self.card(key)
        header.setVisible(bool(present))
        expanded = bool(self.host._component_expanded.get(key, False))
        body.setVisible(bool(present) and expanded)
        button.setText("▼" if expanded else "▶")

    def toggle_card(self, key: str) -> None:
        header, body, button = self.card(key)
        expanded = not bool(self.host._component_expanded.get(key, False))
        self.host._component_expanded[key] = expanded
        body.setVisible(header.isVisible() and expanded)
        button.setText("▼" if expanded else "▶")

    def toggle_dynamic_card(self, key: str, body: Any, button: Any) -> None:
        expanded = not bool(self.host._component_expanded.get(key, False))
        self.host._component_expanded[key] = expanded
        body.setVisible(expanded)
        button.setText("▼" if expanded else "▶")

    def clear(self) -> None:
        h = self.host
        h.inspector_name_label.setText("Nenhum objeto selecionado")
        h.animation_object_label.setText("Nenhum objeto selecionado")
        for key in self.CARD_WIDGETS:
            self.set_card_present(key, False)
        h.add_component_button.setEnabled(False)


class InspectorComponentController:
    """Own mutations and viewport messages for standard Inspector components."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def _selected(self) -> tuple[str, dict[str, Any]] | None:
        h = self.host
        name = h._selected_name
        if h._updating_inspector or name not in h._objects_by_name:
            return None
        return name, h._objects_by_name[name]

    def toggle_renderer(self, checked: bool) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        self.host._record_history()
        obj["renderer_enabled"] = bool(checked)
        self.send_renderer(record_history=False)
        self.host._update_inspector(name)

    def send_renderer(self, record_history: bool = True) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        h = self.host
        if record_history:
            h._record_history()
        obj.update({
            "renderer_enabled": h.show_renderer_chk.isChecked(),
            "texture": h.sprite_texture_field.text().strip(),
            "render_layer": h.sprite_layer_combo.currentText(),
            "sort_order": int(h.sprite_order_field.value()),
        })
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def toggle_audio(self, checked: bool) -> None:
        self._toggle_dictionary_component(
            "audio", checked,
            {"path": "", "volume": 1.0, "loop": False, "autoplay": False},
        )

    def send_audio(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        audio = obj.get("audio")
        if not isinstance(audio, dict):
            return
        h = self.host
        h._record_history()
        chosen = h.audio_path_combo.currentData() or h.audio_path_combo.currentText()
        audio.update({
            "path": "" if chosen == "Nenhum" else chosen,
            "volume": float(h.audio_volume_field.value()),
            "loop": h.audio_loop_field.isChecked(),
            "autoplay": h.audio_autoplay_field.isChecked(),
        })
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def preview_audio(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        audio = obj.get("audio")
        if not isinstance(audio, dict) or not audio.get("path"):
            self.host._log("WARNING", "Selecione um arquivo no Audio Source antes de testar")
            return
        self.host._commands.put({
            "type": "preview_audio", "name": name,
            "path": str(audio["path"]), "volume": float(audio.get("volume", 1.0)),
            "loop": bool(audio.get("loop", False)),
        })

    def toggle_rigidbody(self, checked: bool) -> None:
        self._toggle_dictionary_component(
            "rigidbody", checked,
            {"mass": 1.0, "gravity_scale": 1.0, "use_gravity": True, "is_kinematic": False},
        )

    def toggle_collider(self, checked: bool) -> None:
        self._toggle_dictionary_component("collider", checked, {"type": "box", "is_trigger": False})

    def send_physics(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        rigidbody = obj.get("rigidbody")
        if not isinstance(rigidbody, dict):
            return
        h = self.host
        h._record_history()
        rigidbody.update({
            "use_gravity": h.physics_fields["use_gravity"].isChecked(),
            "is_kinematic": h.physics_fields["is_kinematic"].isChecked(),
        })
        h._commands.put({"type": "set_physics", "name": name, "rigidbody": rigidbody})

    def send_collider(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        collider = obj.get("collider")
        if not isinstance(collider, dict):
            return
        h = self.host
        h._record_history()
        collider_type = str(collider.get("type", "box")).lower()
        keys = (
            ("radius", "offset_x", "offset_y")
            if collider_type == "circle"
            else ("width", "height", "offset_x", "offset_y")
        )
        for key in keys:
            collider[key] = float(h.collider_fields[key].value())
        collider["is_trigger"] = h.collider_trigger_field.isChecked()
        h._commands.put({"type": "set_collider", "name": name, "collider": deepcopy(collider)})

    def toggle_camera(self, checked: bool) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        h = self.host
        h._record_history()
        if checked:
            obj.setdefault("camera", {
                "active": True, "zoom": 1.0, "width": 1280.0, "height": 720.0,
                "background_color": [22, 24, 31], "follow_target": "",
            })
            component_names = obj.setdefault("component_names", [])
            if "Camera2D" not in component_names:
                component_names.append("Camera2D")
        else:
            obj.pop("camera", None)
            obj["component_names"] = [
                value for value in obj.get("component_names", []) if value != "Camera2D"
            ]
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._update_inspector(name)

    def send_camera(self) -> None:
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        camera = obj.get("camera")
        if not isinstance(camera, dict):
            return
        h = self.host
        h._record_history()
        follow = h.camera_follow_combo.currentText()
        camera.update({
            "active": h.camera_active_field.isChecked(),
            "width": float(h.camera_width_field.value()),
            "height": float(h.camera_height_field.value()),
            "zoom": float(h.camera_zoom_field.value()),
            "follow_target": "" if follow == "Nenhum" else follow,
        })
        h._scene_controller.publish_snapshot(h._scene_snapshot)

    def _toggle_dictionary_component(
        self, key: str, checked: bool, default: dict[str, Any]
    ) -> None:
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        h = self.host
        h._record_history()
        if checked:
            obj.setdefault(key, deepcopy(default))
        else:
            obj.pop(key, None)
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._update_inspector(name)
