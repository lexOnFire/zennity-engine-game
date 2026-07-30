"""Transform-tool shortcuts owned by the isolated Pygame viewport."""
from __future__ import annotations

from typing import Any, Callable


class ViewportToolShortcutHandler:
    """Handle Q/W/E/R while keyboard focus belongs to the viewport process."""

    def __init__(self, pygame_module: Any, emit: Callable[[dict], None]) -> None:
        self.pygame = pygame_module
        self.emit = emit
        self._tools = {
            pygame_module.K_q: "select",
            pygame_module.K_w: "move",
            pygame_module.K_e: "rotate",
            pygame_module.K_r: "scale",
        }

    def handle(self, event: Any, *, playing: bool, view_mode: str) -> str | None:
        if playing or view_mode != "scene" or event.type != self.pygame.KEYDOWN:
            return None
        if bool(getattr(event, "repeat", False)):
            return None
        tool = self._tools.get(getattr(event, "key", None))
        if tool is None:
            return None
        self.emit({"type": "tool_changed", "tool": tool})
        return tool
