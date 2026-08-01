"""Component view presenters for the isolated Inspector."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from editor.runtime.native_ui import normalize_ui


class InspectorViewRenderer:
    """Project scene dictionaries into widgets and normalize legacy Animator data."""

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
        h.audio_output_combo.clear()
        h.audio_output_combo.addItem("Padrão do sistema", "")
        for device in h._get_available_audio_outputs():
            h.audio_output_combo.addItem(device, device)
        current_device = str((audio or {}).get("device", ""))
        device_index = h.audio_output_combo.findData(current_device)
        h.audio_output_combo.setCurrentIndex(device_index if device_index >= 0 else 0)
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

    def render_animator(self, name: str, obj: dict[str, Any]) -> None:
        h = self.host
        animator = obj.get("animator")
        h.show_animator_chk.setChecked(animator is not None)
        h.animator_body.setEnabled(True)
        h._refresh_animator_controllers(str((animator or {}).get("controller_path", "")))
        if not animator:
            h._animation_bound_key = None
            h.animator_current_lbl.setText("Nenhum")
            h.animator_preview.setText("Sem Animator")
            return

        clips = h._animation_clips(animator)
        active_clip = str(animator.get("active_clip", next(iter(clips))))
        if active_clip not in clips:
            active_clip = next(iter(clips))
        h.animator_clip_combo.clear()
        h.animator_clip_combo.addItems(list(clips))
        h.animator_clip_combo.setCurrentText(active_clip)
        h.animator_speed_field.setValue(float(animator.get("speed", 1.0)))
        clip = clips[active_clip]
        bound_key = (str(obj.get("id", name)), active_clip)
        if bound_key != h._animation_bound_key:
            h._animation_bound_key = bound_key
            asset_path = str(clip.get("asset_path", ""))
            h._current_animation_asset_path = (
                (Path.cwd() / asset_path).resolve() if asset_path else None
            )
            h._animation_draft_name = active_clip
            h._animation_asset_dirty = False
            h._animation_events = deepcopy(clip.get("events", []))
            h._refresh_animation_events()
            h._update_animation_asset_status()
        h.animator_sheet_combo.clear()
        h.animator_sheet_combo.addItem("Nenhum", "")
        for sheet in h._available_sprite_sheets():
            h.animator_sheet_combo.addItem(Path(sheet).name, sheet)
        sheet_index = h.animator_sheet_combo.findData(str(clip.get("texture", "")))
        h.animator_sheet_combo.setCurrentIndex(max(0, sheet_index))
        h.animator_frame_width.setValue(float(clip.get("frame_width", 32)))
        h.animator_frame_height.setValue(float(clip.get("frame_height", 32)))
        h.animator_start_frame.setValue(float(clip.get("start_frame", 0)))
        h.animator_frame_count.setValue(float(clip.get("frame_count", 1)))
        h.animator_fps_field.setValue(float(clip.get("fps", 8.0)))
        h.animator_loop_field.setChecked(bool(clip.get("loop", True)))
        h.animator_current_lbl.setText(
            str(obj.get("_current_animation_name", animator.get("active_clip", "Idle")))
        )
        h._animator_preview_index = min(
            h._animator_preview_index,
            max(0, int(clip.get("frame_count", 1)) - 1),
        )
        h._refresh_animation_timeline(clip)
        h._update_animation_preview(clip)

    def render_camera(self, name: str, obj: dict[str, Any]) -> None:
        h = self.host
        camera = obj.get("camera") if isinstance(obj.get("camera"), dict) else None
        h._set_inspector_card_present("camera", camera is not None)
        h.show_camera_chk.setChecked(camera is not None)
        h.camera_body.setEnabled(camera is not None)
        h.camera_active_field.setChecked(bool((camera or {}).get("active", True)))
        h.camera_viewport_w.setValue(float((camera or {}).get("width", 1280.0)))
        h.camera_viewport_h.setValue(float((camera or {}).get("height", 720.0)))
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

    def render_ui(self, name: str, obj: dict[str, Any]) -> None:
        h = self.host
        ui = normalize_ui(obj.get("ui"))
        h._set_inspector_card_present("ui", ui is not None)
        if ui is None:
            return
        kind = str(ui["type"])
        labels = {
            "canvas": "🖥 Canvas", "text": "🔤 UI Text",
            "image": "🖼 UI Image", "button": "🔘 UI Button",
            "progress_bar": "📊 UI Progress Bar",
        }
        h.show_ui_chk.setText(labels.get(kind, f"UI {kind.replace('_', ' ').title()}"))
        h.show_ui_chk.setChecked(bool(ui.get("visible", True)))
        h.ui_type_field.setText(
            {
                "canvas": "Canvas", "text": "Texto", "image": "Imagem",
                "button": "Botão", "progress_bar": "Barra de progresso",
            }.get(kind, kind.replace("_", " ").title())
        )
        h.ui_text_field.setText(str(ui.get("text", "")))
        h.ui_text_field.setEnabled(kind in {"text", "button"})
        for key, field in h.ui_position_fields.items():
            field.setValue(float(ui.get(key, 0)))
            field.setEnabled(
                kind != "canvas"
                and (key != "font_size" or kind in {"text", "button"})
                and (key != "alpha" or kind == "image")
            )
        color = tuple(ui.get("color", (255, 255, 255)))[:3]
        h.ui_color_button.setEnabled(kind in {"text", "image", "button", "progress_bar"})
        h.ui_color_button.setStyleSheet(
            f"background: rgb({int(color[0])}, {int(color[1])}, {int(color[2])});"
        )
        h.ui_image_path_field.setText(str(ui.get("path", "")))
        h.ui_image_path_field.setEnabled(kind == "image")
        h.ui_image_button.setEnabled(kind == "image")
        h.ui_interactable_field.setChecked(bool(ui.get("interactable", True)))
        h.ui_interactable_field.setEnabled(kind == "button")
        h.ui_event_field.setText(str(ui.get("event", "click")))
        h.ui_event_field.setEnabled(kind == "button")
        h.ui_target_combo.clear()
        h.ui_target_combo.addItem("Este objeto")
        h.ui_target_combo.addItems([value for value in h._objects_by_name if value != name])
        target = str(ui.get("target", ""))
        h.ui_target_combo.setCurrentText(
            target if target in h._objects_by_name else "Este objeto"
        )
        h.ui_target_combo.setEnabled(kind == "button")

    def render_logic(self, name: str) -> None:
        h = self.host
        bindings = h._logic_workspace_controller.graphs_for_object(name)
        h._set_inspector_card_present("logic", bool(bindings))
        h.logic_graph_combo.clear()
        total_nodes = 0
        for path, graph in bindings:
            total_nodes += len(graph.get("nodes", []))
            suffix = " • via Tag" if str(graph.get("target", {}).get("type", "name")) == "tag" else ""
            h.logic_graph_combo.addItem(f"{graph.get('name', path.stem)}{suffix}", str(path))
        if bindings:
            h.logic_status_label.setText(
                f"{len(bindings)} grafo(s) ativo(s) • {total_nodes} blocos"
            )
            h._logic_workspace_controller.update_summary()
        else:
            h.logic_status_label.setText("Nenhum Logic Graph vinculado")
            h.logic_summary_label.setText(
                "Adicione Lógica Visual para controlar este objeto sem scripts."
            )

    def render_runtime(self, obj: dict[str, Any]) -> None:
        h = self.host
        lifecycle = obj.get("spawn_lifecycle") if isinstance(obj.get("spawn_lifecycle"), dict) else {}
        motions = obj.get("logic_motions") if isinstance(obj.get("logic_motions"), list) else []
        parameters = obj.get("prefab_parameters") if isinstance(obj.get("prefab_parameters"), dict) else {}
        present = h._runtime_playing and (
            bool(obj.get("spawned_by_logic", False)) or bool(lifecycle) or bool(motions) or bool(parameters)
        )
        h._set_inspector_card_present("runtime", present)
        if not present:
            return
        lines = [
            f"Posição: X {float(obj.get('x', 0.0)):.2f}  •  Y {float(obj.get('y', 0.0)):.2f}",
            f"Origem: X {float(lifecycle.get('origin_x', obj.get('x', 0.0))):.2f}  •  Y {float(lifecycle.get('origin_y', obj.get('y', 0.0))):.2f}",
            f"Criado por: {lifecycle.get('creator_object') or 'objeto da cena'}",
            f"Grafo: {lifecycle.get('creator_graph') or '—'}",
        ]
        if lifecycle:
            lines.append(
                f"Idade: {float(lifecycle.get('age', 0.0)):.2f}s  •  Vida: "
                f"{float(lifecycle.get('lifetime', 0.0)):.2f}s"
            )
        if motions:
            lines.append("\nMovimentos ativos:")
            for motion in motions:
                lines.append(
                    f"• {motion.get('name', 'Movement')} [{motion.get('space', 'global')}] "
                    f"X {float(motion.get('x', 0.0)):.2f}  Y {float(motion.get('y', 0.0)):.2f}"
                    + ("  • PAUSADO" if motion.get("paused") else "")
                    + f"\n  Controlado por: {motion.get('graph') or '—'}"
                )
        else:
            lines.append("Movimentos ativos: nenhum")
        if parameters:
            lines.append("\nParâmetros do Prefab:")
            lines.extend(f"• {key}: {value}" for key, value in parameters.items())
        h.runtime_debug_label.setText("\n".join(lines))
