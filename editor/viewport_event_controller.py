"""Editor-side handling of events emitted by the isolated viewport."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


class ViewportEventController:
    """Owns viewport event state transitions and presentation updates."""

    def __init__(self, host: Any) -> None:
        self.host = host

    def selected(self, message: dict) -> None:
        h = self.host
        h._selected_name = message["name"]
        h._update_inspector(h._selected_name)
        h.statusBar().showMessage(f"Viewport: {h._selected_name} selecionado")

    def transform(self, message: dict) -> None:
        h = self.host
        event_type = message.get("type")
        if event_type == "transform_begin":
            h._drag_history_snapshot = deepcopy(h._scene_snapshot)
            return
        if event_type == "transform_end":
            if h._drag_history_snapshot is not None and h._drag_history_snapshot != h._scene_snapshot:
                h._record_history(h._drag_history_snapshot)
            h._drag_history_snapshot = None
            return
        obj = h._objects_by_name.get(message["name"])
        if obj is not None and not h._runtime_playing:
            obj["x"] = float(message["x"])
            obj["y"] = float(message["y"])
            for field in ("w", "h", "rotation"):
                if field in message:
                    obj[field] = float(message[field])
            if message["name"] == h._selected_name:
                h._update_inspector(h._selected_name)
        h.statusBar().showMessage(
            f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
        )

    def play_state(self, message: dict) -> None:
        h = self.host
        state = message["state"]
        if state in {"play", "pause"}:
            h._play_session.set_runtime_state(state)
        if state == "edit":
            h._runtime_objects_by_name.clear()
            h.logic_workspace.clear_runtime_trace()
            h._runtime_animator_states.clear()
            if h._animator_controller_dialog is not None:
                h._animator_controller_dialog.set_runtime_state(None, {})
            h._scene_snapshot, h._selected_name = h._play_session.finish()
            h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
            h._runtime_keys = {key: False for key in h._runtime_keys}
            h._commands.put({"type": "runtime_input", "keys": dict(h._runtime_keys)})
            h._refresh_hierarchy()
            if h._selected_name in h._objects_by_name:
                h._scene_controller.select(h._selected_name)
                h._update_inspector(h._selected_name)
        h._runtime_playing = h._play_session.is_running
        running = state in {"play", "pause"}
        h._set_play_mode_editing_locked(running)
        h.toolbar_actions["Play"].setEnabled(state != "play")
        h.toolbar_actions["Pause"].setEnabled(running)
        h.toolbar_actions["Stop"].setEnabled(running)
        h.logic_workspace.set_play_state(running)
        h.statusBar().showMessage({
            "play": "Viewport: PLAY", "pause": "Viewport: PAUSE",
            "edit": "Viewport: EDIT — cena restaurada",
        }[state])
        h._log("INFO", {
            "play": "Play iniciado/retomado", "pause": "Play pausado",
            "edit": "Play finalizado; cena restaurada",
        }[state])

    def scene_snapshot(self, message: dict) -> None:
        h = self.host
        h._scene_snapshot, restored_selection = h._play_session.consume_scene_snapshot(
            [deepcopy(item) for item in message.get("objects", [])]
        )
        if restored_selection is not None:
            h._selected_name = restored_selection
        h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
        h._refresh_hierarchy()
        if h._selected_name in h._objects_by_name:
            h._update_inspector(h._selected_name)

    def runtime_objects(self, message: dict) -> None:
        h = self.host
        previous_names = set(h._runtime_objects_by_name)
        h._runtime_objects_by_name = {
            str(item.get("name")): deepcopy(item)
            for item in message.get("objects", [])
            if isinstance(item, dict) and item.get("name")
        }
        if set(h._runtime_objects_by_name) != previous_names:
            h._refresh_hierarchy()
        if h._selected_name in h._runtime_objects_by_name:
            h._update_inspector(str(h._selected_name))
        elif h._selected_name in previous_names and h._selected_name not in h._objects_by_name:
            h._selected_name = None
            h._clear_inspector_view()

    def viewport_mode(self, message: dict) -> None:
        state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
        self.host.statusBar().showMessage(f"Viewport {state}")

    def script_log(self, message: dict) -> None:
        self.host._log(
            str(message.get("level", "INFO")), str(message.get("message", ""))
        )

    def logic_trace(self, message: dict) -> None:
        if message.get("type") == "logic_trace":
            self.host.logic_workspace.apply_runtime_trace(dict(message))
        else:
            self.host.logic_workspace.clear_runtime_trace()

    def attach_script(self, message: dict) -> None:
        self.host._attach_script(
            str(message.get("name", "")), Path(str(message.get("path", "")))
        )

    def stats(self, message: dict) -> None:
        h = self.host
        command_stats = h._commands.stats()
        h.profiler_label.setText(
            f"FPS: {message.get('fps', 0):.0f}\n"
            f"Objetos: {message.get('objects', 0)}\n"
            f"Modo: {message.get('mode', 'EDIT')} / {message.get('view', 'SCENE')}\n"
            f"Câmera: {message.get('camera', 'Editor')}\n"
            f"Jogador: {message.get('player') or '—'}\n"
            f"Zoom: {message.get('zoom', 1.0):.2f}\n"
            f"Spawn: {message.get('spawned', 0)} • Reuso: {message.get('reused', 0)} • "
            f"Pool: {message.get('pooled', 0)} • Removidos: {message.get('destroyed', 0)}\n"
            f"IPC: {command_stats['sent']} enviados • {command_stats['coalesced']} unidos"
        )

    def poll(self) -> None:
        h = self.host
        while True:
            try:
                message = h._events.get_nowait()
            except Exception:
                return
            h._viewport_events.dispatch(message)
