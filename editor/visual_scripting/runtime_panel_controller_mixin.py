"""Runtime state, transport, statistics, and replay for the embedded game view."""
from __future__ import annotations

import time
from typing import Any, Optional


class RuntimePanelControllerMixin:
    @property
    def status_badge(self):
        return self.mode_badge

    @property
    def unified_viewport(self):
        return self._canvas

    def set_play_mode(self, is_playing: bool) -> None:
        self.set_viewport_mode(self.VIEWPORT_MODE.GAME if is_playing else self.VIEWPORT_MODE.DEBUG)

    def set_viewport_mode(self, mode: Any) -> None:
        self.viewport_mode = mode
        self._canvas.set_mode(mode)
        if mode == self.VIEWPORT_MODE.GAME:
            self.btn_play.setStyleSheet(self.PLAY_STYLE_ACTIVE)
            self.btn_play.setText("▶  PLAYING")
            self.btn_pause.setEnabled(True)
            self.btn_pause.setStyleSheet(self.PAUSE_STYLE_IDLE)
            self.btn_stop.setEnabled(True)
            self.mode_badge.setText("● PLAYING")
            self.mode_badge.setStyleSheet("color:#00e664;font-size:9px;font-weight:bold;letter-spacing:1px;")
            self._step_bar.hide()
            self.btn_play.setEnabled(False)
        elif mode == self.VIEWPORT_MODE.DEBUG:
            self.btn_play.setStyleSheet(self.PLAY_STYLE_IDLE)
            self.btn_play.setEnabled(True)
            self.btn_pause.setStyleSheet(self.PAUSE_STYLE_ACTIVE)
            self.btn_pause.setText("⏸  PAUSED")
            self.mode_badge.setText("⏸  PAUSED")
            self.mode_badge.setStyleSheet("color:#ffb432;font-size:9px;font-weight:bold;letter-spacing:1px;")
            self._step_bar.show()
        else:
            self.btn_play.setStyleSheet(self.PLAY_STYLE_IDLE)
            self.btn_play.setText("▶  PLAY")
            self.btn_play.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_pause.setStyleSheet(self.PAUSE_STYLE_IDLE)
            self.btn_pause.setText("⏸  PAUSE")
            self.btn_stop.setEnabled(False)
            self.mode_badge.setText("● EDITOR")
            self.mode_badge.setStyleSheet("color:#4c9aff;font-size:9px;font-weight:bold;letter-spacing:1px;")
            self._step_bar.hide()
            self.camera_selector.setCurrentText("Editor Camera")

    def start_play_mode(self) -> None:
        self.camera_selector.setCurrentText("Main Camera")
        self.set_viewport_mode(self.VIEWPORT_MODE.GAME)
        self._notify_play_mode("start_play")

    def toggle_pause_mode(self) -> None:
        if self.viewport_mode == self.VIEWPORT_MODE.GAME:
            self.set_viewport_mode(self.VIEWPORT_MODE.DEBUG)
        elif self.viewport_mode == self.VIEWPORT_MODE.DEBUG:
            self.set_viewport_mode(self.VIEWPORT_MODE.GAME)
            self.btn_pause.setText("⏸  PAUSE")

    def stop_play_mode(self) -> None:
        self.set_viewport_mode(self.VIEWPORT_MODE.EDITOR)
        self._notify_play_mode("stop_play")

    @staticmethod
    def _notify_play_mode(command: str) -> None:
        try:
            from editor.runtime.editor_context import EditorContext
            context = EditorContext.instance()
            play_mode = getattr(context, "play_mode", None) if context else None
            callback = getattr(play_mode, command, None)
            if callable(callback):
                callback()
        except (ImportError, RuntimeError):
            return

    def step_frame(self) -> None:
        if self.viewport_mode == self.VIEWPORT_MODE.DEBUG:
            self._canvas.frame_count += 1
            self._canvas.update()

    def step_node(self) -> None:
        if self.viewport_mode == self.VIEWPORT_MODE.DEBUG:
            self.node_selected_requested.emit(self.active_node_id or "")
            self._canvas.update()

    def apply_live_logic_edit(self, target_object: Any, var_name: str, new_value: Any) -> bool:
        if not target_object:
            return False
        try:
            if hasattr(target_object, var_name):
                setattr(target_object, var_name, new_value)
            elif hasattr(target_object, "variables") and isinstance(target_object.variables, dict):
                target_object.variables[var_name] = new_value
            from editor.runtime.editor_context import EditorContext
            context = EditorContext.instance()
            binding = getattr(context, "property_binding", None) if context else None
            if binding:
                binding.notify_change(target_object, var_name, new_value)
            return True
        except (AttributeError, TypeError, ValueError) as exc:
            print(f"[LiveLogicEditing] {exc}")
            return False

    def highlight_execution_node(self, node_id: str, node_name: str) -> None:
        self.active_node_id = str(node_id)
        self.active_node_name = str(node_name)
        self.highlight_timer = time.time() + 0.6
        self._canvas.active_node_id = self.active_node_id
        self._canvas.active_node_name = self.active_node_name
        self._canvas.highlight_until = self.highlight_timer
        self._canvas._node_flash_until = time.time() + 0.12
        self._canvas.update()

    def set_target_object(self, obj: Any) -> None:
        self.target_object = obj
        self._canvas.update()

    def update_stats(self, fps: Optional[float] = None, physics_ms: Optional[float] = None,
                     scripts_ms: Optional[float] = None, rendering_ms: Optional[float] = None,
                     draw_calls: Optional[int] = None, object_count: Optional[int] = None) -> None:
        if fps is not None:
            self.fps = self._canvas.fps = fps
            self._canvas.push_fps(fps)
            self._lbl_fps.setText(f"FPS {fps:5.1f}")
        if physics_ms is not None:
            self.physics_ms = self._canvas.physics_ms = physics_ms
        if scripts_ms is not None:
            self.scripts_ms = self._canvas.scripts_ms = scripts_ms
        if rendering_ms is not None:
            self.rendering_ms = self._canvas.rendering_ms = rendering_ms
            self._lbl_frame_ms.setText(f"Frame {rendering_ms:.1f}ms")
        if draw_calls is not None:
            self._canvas.draw_calls = draw_calls
            self._lbl_dc.setText(f"DC {draw_calls}")
        if object_count is not None:
            self._canvas.object_count = object_count
            self._lbl_objs.setText(f"Objects {object_count}")

    def _on_canvas_object_clicked(self, obj: dict) -> None:
        self.object_selected.emit(obj)
        node_id = obj.get("node_id", "")
        if node_id:
            self.node_selected_requested.emit(node_id)

    def select_node_by_id(self, node_id: str) -> None:
        self._canvas.active_node_id = node_id
        for obj in self._canvas.game_objects:
            if obj.get("node_id", "") == node_id:
                self._canvas.selected_object_id = obj.get("id", "")
                break
        self._canvas.update()

    def _on_tick(self) -> None:
        now = time.time()
        delta = now - self._canvas.last_frame_time
        self._canvas.last_frame_time = now
        self._canvas.frame_ms = delta * 1000.0
        if self.viewport_mode == self.VIEWPORT_MODE.GAME:
            elapsed = now - self._canvas.play_start_time
            minutes, seconds = int(elapsed) // 60, int(elapsed) % 60
            self._lbl_runtime.setText(f"Runtime {minutes:02d}:{seconds:02d}")
        if not self.is_replaying:
            self.replay_buffer.append({
                "timestamp": now, "node_id": self.active_node_id,
                "node_name": self.active_node_name, "highlight_until": self.highlight_timer,
                "fps": self.fps, "objects": list(self._canvas.game_objects),
                "draw_calls": self._canvas.draw_calls, "object_count": self._canvas.object_count,
            })
            self.timeline_slider.setValue(len(self.replay_buffer))
        self._canvas.update()

    def set_replay_frame(self, index: int) -> None:
        if 0 <= index < len(self.replay_buffer):
            self.is_replaying = True
            self.replay_frame_index = index
            snapshot = self.replay_buffer[index]
            self._canvas.apply_snapshot(snapshot)
            self.active_node_id = snapshot["node_id"]
            self.active_node_name = snapshot["node_name"] or ""
            self.mode_badge.setText(f"⏪  REPLAY  {index}/{len(self.replay_buffer)}")
            self.mode_badge.setStyleSheet("color:#ae7df0;font-size:9px;font-weight:bold;letter-spacing:1px;")

    def resume_live(self) -> None:
        self.is_replaying = False
        self.timeline_slider.setValue(len(self.replay_buffer))
        if self.viewport_mode != self.VIEWPORT_MODE.GAME:
            self.set_viewport_mode(self.VIEWPORT_MODE.GAME)
