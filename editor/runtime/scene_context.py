"""SceneContext — contexto específico de uma cena aberta no editor.

Separa o estado de cena do EditorContext global, evitando que EditorContext
vire um God Object. SceneContext é criado/destruído junto com a cena.
"""
from __future__ import annotations

from typing import Any


class SceneContext:
    """Estado específico de uma cena aberta no editor.

    Responsável por:
    - Viewport (referência ao widget de renderização)
    - Câmera (posição, zoom, modo 2D/3D)
    - Gizmos ativos
    - Objetos editáveis da cena corrente
    - Ferramenta ativa nesta cena
    """

    def __init__(self, scene: Any = None) -> None:
        self.scene = scene
        self.viewport: Any = None
        self.camera_position: list[float] = [0.0, 0.0]
        self.camera_zoom: float = 1.0
        self.camera_mode: str = "2D"
        self.active_tool: str = "select"
        self.gizmos_visible: bool = True
        self.grid_visible: bool = True
        self.grid_size: int = 32
        self._editable_objects: list[Any] = []

    @property
    def editable_objects(self) -> list[Any]:
        if self.scene is not None:
            return list(getattr(self.scene, "editable_objects", []))
        return list(self._editable_objects)

    def set_viewport(self, viewport: Any) -> None:
        self.viewport = viewport

    def set_camera(self, x: float, y: float, zoom: float = 1.0, mode: str = "2D") -> None:
        self.camera_position = [x, y]
        self.camera_zoom = zoom
        self.camera_mode = mode

    def set_active_tool(self, tool_id: str) -> None:
        self.active_tool = tool_id
        try:
            from editor.core.event_bus import EventBus
            EventBus.emit("Scene.tool_changed", tool_id=tool_id)
        except Exception:
            pass

    def snapshot(self) -> dict:
        """Retorna o estado atual como dicionário serializável para persistência de workspace."""
        return {
            "camera_position": self.camera_position,
            "camera_zoom": self.camera_zoom,
            "camera_mode": self.camera_mode,
            "active_tool": self.active_tool,
            "gizmos_visible": self.gizmos_visible,
            "grid_visible": self.grid_visible,
            "grid_size": self.grid_size,
        }

    def restore(self, data: dict) -> None:
        """Restaura estado a partir de snapshot de workspace."""
        self.camera_position = data.get("camera_position", [0.0, 0.0])
        self.camera_zoom = data.get("camera_zoom", 1.0)
        self.camera_mode = data.get("camera_mode", "2D")
        self.active_tool = data.get("active_tool", "select")
        self.gizmos_visible = data.get("gizmos_visible", True)
        self.grid_visible = data.get("grid_visible", True)
        self.grid_size = data.get("grid_size", 32)
