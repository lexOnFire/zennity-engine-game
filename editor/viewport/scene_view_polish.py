from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SceneViewPolishState:
    """Estado leve e testavel para controles de polish da Scene View.

    Esta classe nao conhece Runtime, GameObject concreto ou PySide. Ela guarda
    apenas preferencias de visualizacao que a Viewport pode consultar.
    """

    grid_visible: bool = True
    gizmos_visible: bool = True
    overlays_visible: bool = True
    selection_outline_visible: bool = True
    grid_size: int = 32
    active_tool: str = "select"
    view_mode: str = "scene"
    hidden_gizmo_types: set[str] = field(default_factory=set)

    def set_grid_visible(self, visible: bool) -> None:
        self.grid_visible = bool(visible)

    def set_gizmos_visible(self, visible: bool) -> None:
        self.gizmos_visible = bool(visible)

    def set_overlays_visible(self, visible: bool) -> None:
        self.overlays_visible = bool(visible)

    def set_selection_outline_visible(self, visible: bool) -> None:
        self.selection_outline_visible = bool(visible)

    def set_grid_size(self, size: int | float) -> None:
        self.grid_size = max(1, int(size))

    def set_active_tool(self, tool: str) -> None:
        self.active_tool = str(tool or "select").lower()

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = "game" if str(mode).lower() == "game" else "scene"

    def is_game_view(self) -> bool:
        return self.view_mode == "game"

    def hide_gizmo_type(self, component_type: str) -> None:
        name = str(component_type or "").strip()
        if name:
            self.hidden_gizmo_types.add(name)

    def show_gizmo_type(self, component_type: str) -> None:
        self.hidden_gizmo_types.discard(str(component_type or "").strip())

    def should_draw_gizmo(self, component_type: str, is_playing: bool = False) -> bool:
        if is_playing or self.is_game_view() or not self.gizmos_visible:
            return False
        return str(component_type or "") not in self.hidden_gizmo_types

    def toolbar_state(self) -> dict[str, Any]:
        """Retorna um snapshot simples para toolbars e testes."""
        return {
            "tool": self.active_tool,
            "grid_visible": self.grid_visible,
            "gizmos_visible": self.gizmos_visible,
            "overlays_visible": self.overlays_visible,
            "selection_outline_visible": self.selection_outline_visible,
            "grid_size": self.grid_size,
            "view_mode": self.view_mode,
            "hidden_gizmo_types": sorted(self.hidden_gizmo_types),
        }


def focus_selected_camera_position(selected: Any) -> tuple[float, float] | None:
    """Calcula o alvo de foco para a Scene View sem mutar o Runtime.

    Retorna None quando nao ha objeto selecionado ou Transform valido.
    """
    transform = getattr(selected, "transform", None)
    if transform is None:
        return None
    position = getattr(transform, "position", None)
    if position is None or len(position) < 2:
        return None
    return float(position[0]), float(position[1])
