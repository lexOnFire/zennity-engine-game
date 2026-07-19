"""Read-only component view renderers for the isolated Inspector."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class InspectorViewRenderer:
    """Project scene dictionaries into Inspector widgets without mutating the scene."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def render_identity_transform(self, name: str, obj: dict[str, Any]) -> None:
        h = self.host
        h.inspector_name_label.setText(name)
        h.animation_object_label.setText(name)
        h.add_component_button.setEnabled(not h._runtime_playing)
        h._set_inspector_card_present("transform", True)
        for key in ("x", "y", "w", "h", "rotation"):
            h.inspector_fields[key].setValue(float(obj[key]))

    def render_renderer(self, obj: dict[str, Any]) -> None:
        h = self.host
        enabled = bool(obj.get("renderer_enabled", True))
        present = (
            enabled
            and obj.get("mesh_type") != "UI"
            and not isinstance(obj.get("camera"), dict)
        )
        h._set_inspector_card_present("sprite", present)
        h.show_renderer_chk.setChecked(enabled)
        h.sprite_renderer_body.setEnabled(enabled)
        h.sprite_texture_field.setText(str(obj.get("texture", "")))
        color = tuple(obj.get("color", (255, 255, 255)))
        h.sprite_color_button.setStyleSheet(
            f"background: rgb({int(color[0])}, {int(color[1])}, {int(color[2])});"
        )
        layer = str(obj.get("render_layer", "Default"))
        if h.sprite_layer_combo.findText(layer) < 0:
            h.sprite_layer_combo.addItem(layer)
        h.sprite_layer_combo.setCurrentText(layer)
        h.sprite_order_field.setValue(float(obj.get("sort_order", 0)))

    def render_audio(self, obj: dict[str, Any]) -> None:
        h = self.host
        audio = obj.get("audio") if isinstance(obj.get("audio"), dict) else None
        h._set_inspector_card_present("audio", audio is not None)
        h.show_audio_chk.setChecked(audio is not None)
        h.audio_source_body.setEnabled(audio is not None)
        h.audio_path_combo.clear()
        h.audio_path_combo.addItem("Nenhum", "")
        current_path = str((audio or {}).get("path", ""))
        for path in h._get_available_audio_files():
            h.audio_path_combo.addItem(Path(path).name, path)
        if audio:
            index = h.audio_path_combo.findData(current_path)
            h.audio_path_combo.setCurrentIndex(index if index >= 0 else 0)
        h.audio_volume_field.setValue(float((audio or {}).get("volume", 1.0)))
        h.audio_loop_field.setChecked(bool((audio or {}).get("loop", False)))
        h.audio_autoplay_field.setChecked(bool((audio or {}).get("autoplay", False)))

    def render_physics(self, obj: dict[str, Any]) -> None:
        h = self.host
        rigidbody = obj.get("rigidbody")
        h._set_inspector_card_present("rigidbody", rigidbody is not None)
        h.show_rigidbody_chk.setChecked(rigidbody is not None)
        for key, field in h.physics_fields.items():
            field.setEnabled(rigidbody is not None)
            field.setChecked(bool((rigidbody or {}).get(key, False)))

        collider = obj.get("collider") if isinstance(obj.get("collider"), dict) else None
        h._set_inspector_card_present("collider", collider is not None)
        h.show_collider_chk.setChecked(collider is not None)
        collider_type = str((collider or {}).get("type", "box")).lower()
        defaults = {
            "width": float(obj["w"]), "height": float(obj["h"]),
            "radius": min(float(obj["w"]), float(obj["h"])) / 2.0,
            "offset_x": 0.0, "offset_y": 0.0,
        }
        for key, field in h.collider_fields.items():
            relevant = (
                collider is not None
                and (key not in ("width", "height") or collider_type == "box")
                and (key != "radius" or collider_type == "circle")
            )
            field.setEnabled(relevant)
            field.setValue(float((collider or {}).get(key, defaults[key])))
        h.collider_trigger_field.setEnabled(collider is not None)
        h.collider_trigger_field.setChecked(bool((collider or {}).get("is_trigger", False)))

    def render_camera(self, name: str, obj: dict[str, Any]) -> None:
        h = self.host
        camera = obj.get("camera") if isinstance(obj.get("camera"), dict) else None
        h._set_inspector_card_present("camera", camera is not None)
        h.show_camera_chk.setChecked(camera is not None)
        h.camera_body.setEnabled(camera is not None)
        h.camera_active_field.setChecked(bool((camera or {}).get("active", True)))
        h.camera_width_field.setValue(float((camera or {}).get("width", 1280.0)))
        h.camera_height_field.setValue(float((camera or {}).get("height", 720.0)))
        h.camera_zoom_field.setValue(float((camera or {}).get("zoom", 1.0)))
        follow_target = str((camera or {}).get("follow_target", ""))
        h.camera_follow_combo.clear()
        h.camera_follow_combo.addItem("Nenhum")
        for object_name in h._objects_by_name:
            if object_name != name:
                h.camera_follow_combo.addItem(object_name)
        h.camera_follow_combo.setCurrentText(
            follow_target if follow_target in h._objects_by_name else "Nenhum"
        )
        background = (camera or {}).get("background_color", [22, 24, 31])
        h.camera_color_button.setStyleSheet(
            f"background: rgb({int(background[0])}, {int(background[1])}, {int(background[2])});"
        )
