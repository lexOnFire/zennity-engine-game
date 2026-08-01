"""Window, UI and camera navigation events for the isolated viewport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ViewportNavigationState:
    running: bool
    panning: bool
    pan_last: tuple[int, int]
    camera_x: float
    camera_y: float
    zoom: float


class ViewportNavigationEventHandler:
    def __init__(
        self,
        pygame: Any,
        objects: dict[str, dict[str, Any]],
        native_ui: Any,
        emit: Callable[[dict[str, Any]], None],
        screen_to_world: Callable[[float, float], tuple[float, float]],
    ) -> None:
        self.pygame = pygame
        self.objects = objects
        self.native_ui = native_ui
        self.emit = emit
        self.screen_to_world = screen_to_world

    def handle(
        self,
        event: Any,
        state: ViewportNavigationState,
        *,
        playing: bool,
        view_mode: str,
    ) -> tuple[bool, ViewportNavigationState]:
        pg = self.pygame
        if event.type == pg.QUIT:
            state.running = False
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and playing and view_mode == "game":
            self._dispatch_ui_click(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 2 and not playing and view_mode == "scene":
            state.panning = True
            state.pan_last = event.pos
        elif event.type == pg.MOUSEBUTTONUP and event.button == 2:
            state.panning = False
        elif event.type == pg.MOUSEWHEEL and not playing and view_mode == "scene":
            mouse_x, mouse_y = pg.mouse.get_pos()
            world_x, world_y = self.screen_to_world(float(mouse_x), float(mouse_y))
            state.zoom = max(0.25, min(4.0, state.zoom * (1.12 ** event.y)))
            state.camera_x = world_x - mouse_x / state.zoom
            state.camera_y = world_y - mouse_y / state.zoom
        elif event.type == pg.MOUSEMOTION and state.panning and not playing and view_mode == "scene":
            state.camera_x -= (event.pos[0] - state.pan_last[0]) / state.zoom
            state.camera_y -= (event.pos[1] - state.pan_last[1]) / state.zoom
            state.pan_last = event.pos
        else:
            return False, state
        return True, state

    def _dispatch_ui_click(self, position: tuple[int, int]) -> None:
        clicked = self.native_ui.button_at(self.objects, position)
        if clicked is None:
            return
        owner, ui = clicked
        target_name = str(ui.get("target", "")) or str(owner.get("name", ""))
        target = self.objects.get(target_name)
        event_name = str(ui.get("event", "click")) or "click"
        if target is not None:
            target.setdefault("script_instructions", []).append({
                "command": event_name,
                "value": {"source": owner.get("name"), "type": "ui_button"},
            })
        self.emit({
            "type": "script_log", "level": "INFO",
            "message": f"UI Button: {owner.get('name')} → {target_name}.{event_name}",
        })
