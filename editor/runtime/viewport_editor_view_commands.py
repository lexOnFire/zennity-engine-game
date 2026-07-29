"""Editor-only viewport view commands such as focus and grid visibility."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ViewportEditorViewState:
    selected_name: str | None
    camera_x: float
    camera_y: float
    zoom: float
    show_grid: bool


class ViewportEditorViewCommandHandler:
    """Handles non-mutating editor viewport commands."""

    COMMAND_TYPES = frozenset({"focus_selected", "toggle_grid"})

    def __init__(
        self,
        objects: dict[str, dict[str, Any]],
        viewport_size: Any,
    ) -> None:
        self.objects = objects
        self.viewport_size = viewport_size

    def handle(
        self,
        command: dict[str, Any],
        state: ViewportEditorViewState,
    ) -> ViewportEditorViewState | None:
        command_type = str(command.get("type", ""))
        if command_type not in self.COMMAND_TYPES:
            return None
        if command_type == "toggle_grid":
            return ViewportEditorViewState(
                state.selected_name,
                state.camera_x,
                state.camera_y,
                state.zoom,
                not state.show_grid,
            )
        selected = self.objects.get(str(state.selected_name)) if state.selected_name else None
        if selected is None:
            return state
        width, height = self.viewport_size()
        return ViewportEditorViewState(
            state.selected_name,
            float(selected.get("x", 0.0)) - width / (2.0 * state.zoom),
            float(selected.get("y", 0.0)) - height / (2.0 * state.zoom),
            state.zoom,
            state.show_grid,
        )
