"""Animation asset, controller, preview and binding operations."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTreeWidgetItem

from editor.runtime.sprite_rendering import assign_sprite_texture
from editor.ui.icons import editor_icon
from editor.widgets.animation_picker import AnimationPickerDialog
from editor.widgets.animator_controller_editor import AnimatorControllerEditorDialog
from engine.animation.clip_asset import animation_asset_from_clip, animation_asset_to_clip, default_animation_asset, load_animation_asset, save_animation_asset
from engine.animation.controller_asset import load_animator_controller


class AnimationPreviewOperations:
    def _mark_animation_asset_dirty(self, *_args) -> None:
        self._animation_workspace.mark_dirty()

    def _update_animation_asset_status(self) -> None:
        self._animation_workspace.update_status()

    def _animation_frame_count(self) -> int:
        return self._animation_workspace.frame_count()

    def _refresh_animation_timeline(self, clip: dict) -> None:
        self._animation_workspace.refresh_timeline(clip)

    def _set_animation_preview_frame(self, index: int) -> None:
        self._animation_workspace.set_preview_frame(index)

    def _refresh_animation_events(self) -> None:
        self.animation_events_tree.clear()
        ordered = sorted(self._animation_events, key=lambda item: (int(item.get("frame", 0)), str(item.get("name", ""))))
        for event in ordered:
            payload = event.get("payload")
            QTreeWidgetItem(self.animation_events_tree, [str(int(event.get("frame", 0)) + 1), str(event.get("name", "")), "" if payload is None else str(payload)])
        markers = ", ".join(f'F{int(event.get("frame", 0)) + 1}:{event.get("name", "")}' for event in ordered)
        self.animation_timeline.setToolTip("Arraste para visualizar qualquer quadro" + (f"\nEventos: {markers}" if markers else "\nSem eventos"))

    def _add_animation_event(self) -> None:
        name, ok = QInputDialog.getText(self, "Evento de Animação", "Nome do evento:", text="evento")
        name = name.strip()
        if not ok or not name:
            return
        payload, ok = QInputDialog.getText(self, "Evento de Animação", "Payload opcional:")
        if not ok:
            return
        self._animation_events.append({
            "frame": int(self._animator_preview_index), "name": name,
            "payload": payload if payload else None,
        })
        self._animation_asset_dirty = True
        self._refresh_animation_events()
        self._update_animation_asset_status()

    def _remove_animation_event(self) -> None:
        index = self.animation_events_tree.indexOfTopLevelItem(self.animation_events_tree.currentItem())
        if index < 0:
            return
        ordered = sorted(range(len(self._animation_events)), key=lambda item: (int(self._animation_events[item].get("frame", 0)), str(self._animation_events[item].get("name", ""))))
        self._animation_events.pop(ordered[index])
        self._animation_asset_dirty = True
        self._refresh_animation_events()
        self._update_animation_asset_status()

    def _toggle_animation_preview_playback(self) -> None:
        self._animation_workspace.toggle_preview()

    def _refresh_animation_frame_editor_from_fields(self, *_args) -> None:
        texture = str(self.animator_sheet_combo.currentData() or "")
        path = Path(texture)
        if texture and not path.is_absolute():
            path = Path.cwd() / path
        self.animation_frame_editor.set_source(
            path if texture else "",
            int(self.animator_frame_width.value()),
            int(self.animator_frame_height.value()),
            list(self._animation_frames),
        )
        if not self._updating_inspector:
            self._mark_animation_asset_dirty()
            self._set_animation_preview_frame(self._animator_preview_index)

    def _reset_animation_frames_from_range(self, *_args) -> None:
        if self._updating_inspector:
            return
        start = max(0, int(self.animator_start_frame.value()))
        count = max(1, int(self.animator_frame_count.value()))
        self._animation_frames = list(range(start, start + count))
        self.animation_frame_editor.set_frames(self._animation_frames)
        self._animation_asset_dirty = True
        self._animator_preview_index = min(self._animator_preview_index, count - 1)
        self._refresh_animation_timeline(animation_asset_to_clip(self._animation_asset_from_editor()))
        self._set_animation_preview_frame(self._animator_preview_index)
        self._update_animation_asset_status()

    def _set_animation_frames(self, frames: list[int]) -> None:
        if self._updating_inspector:
            return
        normalized = [max(0, int(frame)) for frame in frames] or [0]
        self._animation_frames = normalized
        self.animator_start_frame.blockSignals(True)
        self.animator_frame_count.blockSignals(True)
        self.animator_start_frame.setValue(float(normalized[0]))
        self.animator_frame_count.setValue(float(len(normalized)))
        self.animator_start_frame.blockSignals(False)
        self.animator_frame_count.blockSignals(False)
        self._animation_asset_dirty = True
        self._animator_preview_index = min(self._animator_preview_index, len(normalized) - 1)
        clip = animation_asset_to_clip(self._animation_asset_from_editor())
        self._refresh_animation_timeline(clip)
        self._set_animation_preview_frame(self._animator_preview_index)
        self._update_animation_asset_status()

    def _add_animation_clip(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        animator = self._objects_by_name[self._selected_name].get("animator")
        if not isinstance(animator, dict):
            return
        name, accepted = QInputDialog.getText(self, "Novo Clip", "Nome do clip:", text="NewClip")
        name = name.strip()
        clips = self._animation_clips(animator)
        if not accepted or not name or name in clips:
            return
        self._record_history()
        clips[name] = self._default_animation_clip()
        animator["active_clip"] = name
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._update_inspector(self._selected_name)

    def _remove_animation_clip(self) -> None:
        if self._selected_name not in self._objects_by_name:
            return
        animator = self._objects_by_name[self._selected_name].get("animator")
        if not isinstance(animator, dict):
            return
        clips = self._animation_clips(animator)
        name = self.animator_clip_combo.currentText()
        if name not in clips or len(clips) <= 1:
            return
        self._record_history()
        clips.pop(name)
        animator["active_clip"] = next(iter(clips))
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._update_inspector(self._selected_name)

    def _tick_animation_preview(self) -> None:
        if not self._animation_preview_playing or not self.animation_window.isVisible():
            return
        animator = None
        clip = None
        if self._selected_name in self._objects_by_name:
            animator = self._objects_by_name[self._selected_name].get("animator")
            if isinstance(animator, dict):
                clips = self._animation_clips(animator)
                clip = clips.get(self.animator_clip_combo.currentText())
        if not isinstance(clip, dict):
            clip = animation_asset_to_clip(self._animation_asset_from_editor())
        frames = clip.get("frames")
        count = max(1, len(frames) if isinstance(frames, list) and frames else int(clip.get("frame_count", 1)))
        if clip.get("loop", True):
            self._animator_preview_index = (self._animator_preview_index + 1) % count
        else:
            self._animator_preview_index = min(count - 1, self._animator_preview_index + 1)
        speed = float(animator.get("speed", 1.0)) if isinstance(animator, dict) else 1.0
        fps = max(0.1, float(clip.get("fps", 8.0))) * max(0.01, speed)
        self._animator_preview_timer.setInterval(max(16, int(1000.0 / fps)))
        self._update_animation_preview(clip, self._animator_preview_index)
        self.animation_timeline.blockSignals(True)
        self.animation_timeline.setValue(self._animator_preview_index)
        self.animation_timeline.blockSignals(False)
        self.animation_frame_label.setText(f"Frame {self._animator_preview_index + 1} / {count}")

    def _update_animation_preview(self, clip: dict, frame_offset: int = 0) -> None:
        texture = str(clip.get("texture", ""))
        path = Path(texture)
        if texture and not path.is_absolute():
            path = Path.cwd() / path
        pixmap = QPixmap(str(path)) if texture else QPixmap()
        width = max(1, int(clip.get("frame_width", 32)))
        height = max(1, int(clip.get("frame_height", 32)))
        if pixmap.isNull() or width > pixmap.width() or height > pixmap.height():
            self.animator_preview.clear()
            self._set_animation_preview_state("empty" if not texture else "error")
            self.animator_preview.setText(
                "Selecione um Sprite Sheet nas propriedades"
                if not texture else "Sprite Sheet inválido ou frame maior que a imagem"
            )
            return
        columns = max(1, pixmap.width() // width)
        frames = clip.get("frames")
        if isinstance(frames, list) and frames:
            frame = max(0, int(frames[min(max(0, int(frame_offset)), len(frames) - 1)]))
        else:
            frame = max(0, int(clip.get("start_frame", 0))) + max(0, int(frame_offset))
        x = (frame % columns) * width
        y = (frame // columns) * height
        if x + width > pixmap.width() or y + height > pixmap.height():
            self.animator_preview.clear()
            self._set_animation_preview_state("error")
            self.animator_preview.setText("Quadro fora da imagem")
            return
        preview = pixmap.copy(x, y, width, height)
        self._set_animation_preview_state("content")
        self.animator_preview.setPixmap(preview.scaled(120, 90, Qt.KeepAspectRatio, Qt.FastTransformation))

    def _set_animation_preview_state(self, state: str) -> None:
        if self.animator_preview.property("uiState") == state:
            return
        self.animator_preview.setProperty("uiState", state)
        self.animator_preview.style().unpolish(self.animator_preview)
        self.animator_preview.style().polish(self.animator_preview)

    def _send_inspector_animator(self) -> None:
        if self._updating_inspector or self._selected_name not in self._objects_by_name:
            return
        obj = self._objects_by_name[self._selected_name]
        anim = obj.get("animator")
        if anim is None:
            return
        self._record_history()
        clip_name = self.animator_clip_combo.currentText() or "Idle"
        clips = self._animation_clips(anim)
        clip = clips.setdefault(clip_name, self._default_animation_clip())
        anim["active_clip"] = clip_name
        anim["speed"] = float(self.animator_speed_field.value())
        texture = self.animator_sheet_combo.currentData() or ""
        clip.update({
            "texture": str(texture),
            "frame_width": int(self.animator_frame_width.value()),
            "frame_height": int(self.animator_frame_height.value()),
            "start_frame": int(self.animator_start_frame.value()),
            "frame_count": int(self.animator_frame_count.value()),
            "fps": float(self.animator_fps_field.value()),
            "loop": self.animator_loop_field.isChecked(),
        })
        clip["frames"] = list(range(clip["start_frame"], clip["start_frame"] + clip["frame_count"]))
        self._scene_controller.publish_snapshot(self._scene_snapshot)
        self._update_inspector(self._selected_name)

    def _choose_animation_component(self) -> None:
        """Escolhe um ``.zanim`` antes de criar o Animator no objeto."""
        object_name = self._selected_name
        if object_name not in self._objects_by_name:
            return
        picker = AnimationPickerDialog(Path.cwd(), self)
        if not picker.exec():
            return
        if picker.requested_action == "create":
            self._show_animation_window()
            self._new_animation_asset()
            return
        if picker.requested_action == "empty":
            if isinstance(self._objects_by_name[object_name].get("animator"), dict):
                self.statusBar().showMessage(f"{object_name} já possui um Animator 2D")
                return
            self._record_history()
            self._objects_by_name[object_name]["animator"] = {
                "active_clip": "Idle", "speed": 1.0,
                "clips": {"Idle": self._default_animation_clip()},
            }
            self._scene_controller.publish_snapshot(self._scene_snapshot)
            self._update_inspector(object_name)
            self._log("INFO", f"Animator vazio adicionado em {object_name}")
            return
        if picker.requested_action == "select" and picker.selected_path is not None:
            if self._apply_animation_asset_path_to_object(picker.selected_path, object_name):
                self._log("INFO", f"Animator adicionado em {object_name} com {picker.selected_path.name}")

    def _handle_animator_state_event(self, message: dict) -> None:
        object_name = str(message.get("name", ""))
        self._runtime_animator_states[object_name] = dict(message)
        if object_name == self._selected_name:
            state = str(message.get("state", "Nenhum"))
            self.animator_current_lbl.setText(state)
            if self._animator_controller_dialog is not None:
                self._animator_controller_dialog.set_runtime_state(state, message.get("parameters"))

    def _handle_animation_event(self, message: dict) -> None:
        self._log(
            "INFO",
            f"Evento de animação: {message.get('name')} → {message.get('event')} "
            f"(frame {int(message.get('frame', 0)) + 1})",
        )


