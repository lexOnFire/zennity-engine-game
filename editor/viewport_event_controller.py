"""Editor-side handling of events emitted by the isolated viewport."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


class ViewportEventController:
    """Owns viewport event state transitions and presentation updates."""

    MAX_EVENTS_PER_POLL = 256
    PRIORITY_SCAN_LIMIT = 1024
    COALESCED_EVENT_TYPES = frozenset({"runtime_objects", "stats", "runtime_metrics", "transform"})
    PRIORITY_EVENT_TYPES = frozenset({"load_scene", "open_scene"})

    def __init__(self, host: Any) -> None:
        self.host = host

    def selected(self, message: dict) -> None:
        if hasattr(self.host, "_play_session") and getattr(self.host._play_session, "is_running", False):
            return
        self.host._selection.select(str(message["name"]), source="Viewport")

    def tool_changed(self, message: dict) -> None:
        """Mirror a shortcut handled by the focused Pygame viewport."""
        self.host._tool_controller.activate_tool(str(message["tool"]))

    def delete_selected_requested(self, _message: dict) -> None:
        """Delete the editor selection when Delete was pressed in native viewport."""
        h = self.host
        if h._play_session.is_running:
            return
        selected = h._selected_name
        if selected in h._objects_by_name:
            h._scene_objects.delete(selected)

    def transform(self, message: dict) -> None:
        h = self.host
        event_type = message.get("type")
        obj = h._objects_by_name.get(message.get("name"))
        if obj is not None and obj.get("editor_locked", False):
            h._drag_history_snapshot = None
            h._scene_controller.publish_snapshot(h._scene_snapshot)
            if h._selected_name == message.get("name"):
                h._scene_controller.select(h._selected_name)
            h.statusBar().showMessage(f"{message['name']} está com a transformação travada")
            return
        if event_type == "transform_begin":
            h._drag_history_snapshot = deepcopy(h._scene_snapshot)
            return
        if event_type == "transform_end":
            if h._drag_history_snapshot is not None and h._drag_history_snapshot != h._scene_snapshot:
                h._record_history(h._drag_history_snapshot)
            h._drag_history_snapshot = None
            if message.get("name") == h._selected_name:
                h._update_inspector(h._selected_name)
            return
        obj = h._objects_by_name.get(message["name"])
        if obj is not None and not h._runtime_playing:
            obj["x"] = float(message["x"])
            obj["y"] = float(message["y"])
            for field in ("w", "h", "rotation"):
                if field in message:
                    obj[field] = float(message[field])
            if message["name"] == h._selected_name:
                h._update_transform_fields_only(message["name"], obj)
        h.statusBar().showMessage(
            f"Viewport: {message['name']} em X={message['x']:.1f}, Y={message['y']:.1f}"
        )

    def play_state(self, message: dict) -> None:
        h = self.host
        state = message["state"]
        if state in {"play", "pause"}:
            h._play_session.set_runtime_state(state)
        if state == "edit":
            h._runtime_stopping = False
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
        if running:
            h._runtime_stopping = False
        h._set_play_mode_editing_locked(running)
        h.toolbar_actions["Play"].setEnabled(state != "play")
        h.toolbar_actions["Pause"].setEnabled(running)
        h.toolbar_actions["Stop"].setEnabled(running)
        h.logic_workspace.set_play_state(running)
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None and hasattr(dock, "set_play_state"):
            dock.set_play_state(state)
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
        if (
            message.get("source") == "stop_restore"
            and not h._play_session.is_running
            and not h._play_session.has_restore_pending
        ):
            return
        h._scene_snapshot, restored_selection = h._play_session.consume_scene_snapshot(
            [deepcopy(item) for item in message.get("objects", [])]
        )
        if restored_selection is not None:
            h._selected_name = restored_selection
        h._objects_by_name = {item["name"]: item for item in h._scene_snapshot}
        h._refresh_hierarchy()
        if h._selected_name in h._objects_by_name:
            h._update_inspector(h._selected_name)
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None:
            dock.sync_from_host()

    def runtime_objects(self, message: dict) -> None:
        h = self.host
        previous_names = set(h._runtime_objects_by_name)
        previous_selected = h._runtime_objects_by_name.get(h._selected_name)
        h._runtime_objects_by_name = {
            str(item.get("name")): deepcopy(item)
            for item in message.get("objects", [])
            if isinstance(item, dict) and item.get("name")
        }
        if set(h._runtime_objects_by_name) != previous_names:
            h._refresh_hierarchy()
        current_selected = h._runtime_objects_by_name.get(h._selected_name)
        if current_selected is not None and current_selected != previous_selected:
            h._update_inspector(str(h._selected_name))
        elif h._selected_name in previous_names and h._selected_name not in h._objects_by_name:
            h._selected_name = None
            h._clear_inspector_view()
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None and (not hasattr(dock, "isVisible") or dock.isVisible()):
            dock.sync_from_host()

    def viewport_mode(self, message: dict) -> None:
        state = "embutida" if message.get("embedded") else "em janela separada (fallback)"
        self.host.statusBar().showMessage(f"Viewport {state}")

    def runtime_log(self, message: dict) -> None:
        self.host._log(
            str(message.get("level", "INFO")), str(message.get("message", ""))
        )

    def logic_trace(self, message: dict) -> None:
        if message.get("type") == "logic_trace":
            self.host.logic_workspace.apply_runtime_trace(dict(message))
        else:
            self.host.logic_workspace.clear_runtime_trace()
        dock = getattr(self.host, "_dock_visual_scripting", None)
        if dock is not None and hasattr(dock, "apply_runtime_trace"):
            dock.apply_runtime_trace(message)
        bt_ctrl = getattr(self.host, "_behavior_tree_controller", None)
        if bt_ctrl is not None and hasattr(bt_ctrl, "apply_runtime_trace"):
            bt_ctrl.apply_runtime_trace(message)
        orchestrator = getattr(self.host, "bridge_orchestrator", None)
        if orchestrator is not None:
            bt_mode = getattr(orchestrator, "behavior_tree", None)
            bt_dock = getattr(bt_mode, "dock", None) if bt_mode else None
            if bt_dock is not None and hasattr(bt_dock, "apply_runtime_trace"):
                bt_dock.apply_runtime_trace(message)

    def stats(self, message: dict) -> None:
        h = self.host
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None:
            dock.mini_viewport.update_stats(
                fps=float(message.get("fps", 0.0)),
                object_count=int(message.get("objects", 0)),
            )
            dock.update_runtime_stats(
                fps=float(message.get("fps", 0.0)),
                object_count=int(message.get("objects", 0)),
                frame_ms=message.get("frame_ms"),
            )
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

    def runtime_metrics(self, message: dict) -> None:
        from editor.core.event_bus import EventBus
        EventBus.emit("runtime_metrics", **message)

    def poll(self) -> None:
        h = self.host
        pending: dict[str, dict] = {}
        processed = 0

        def dispatch_pending() -> None:
            for queued_message in pending.values():
                h._viewport_events.dispatch(queued_message)
            pending.clear()

        while processed < self.PRIORITY_SCAN_LIMIT:
            try:
                message = h._events.get_nowait()
            except Exception:
                break
            processed += 1
            event_type = str(message.get("type", ""))
            if event_type in self.COALESCED_EVENT_TYPES:
                pending[event_type] = message
            else:
                # Preserve event boundaries such as play/stop: snapshots queued
                # before a state transition must be observed before it.
                dispatch_pending()
                h._viewport_events.dispatch(message)
        dispatch_pending()
