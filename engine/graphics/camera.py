from __future__ import annotations
from typing import Optional, Any
import numpy as np
from engine.core.component import Component


class CameraMeta(type):
    @property
    def main(cls) -> Optional[Camera]:
        """Atalho estático para obter a câmera principal ativa."""
        from engine.graphics.camera_manager import CameraManager
        return CameraManager.get_main_camera()


class Camera(Component, metaclass=CameraMeta):
    """
    Componente Camera oficial da Zennity Engine — fonte de verdade para câmeras
    de gameplay: é a única registrada em engine/core/component_registry.py
    (serializável em .zscene), a única usada pelo pipeline de build/runtime
    (engine/runtime/runtime_scene.py) e a única presente nas cenas reais do
    projeto. Suporta múltiplas câmeras via CameraManager (priority/active) e
    viewport parcial (split-screen).

    Ver também engine/graphics/camera2d.py (Camera2D) — classe legada mantida
    para follow-target/bounds embutidos (usados por demos/) e para a câmera de
    viewport do editor (editor/viewport/viewport_camera.py), que não é um
    GameObject de cena. Código de renderização deve resolver a câmera ativa via
    engine.graphics.active_camera.get_active_camera(), não reimplementar o
    fallback Camera.main/Camera2D.main manualmente.
    """
    component_type = "Camera"
    unique = True

    def __init__(
        self,
        zoom: float = 1.0,
        clear_color: tuple[int, int, int] = (30, 30, 30),
        viewport_rect: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0),
        priority: int = 0,
        active: bool = True
    ) -> None:
        super().__init__()
        self.zoom = float(zoom)
        self.clear_color = tuple(clear_color)
        self.viewport_rect = tuple(viewport_rect)
        self.priority = int(priority)
        self._active_state = bool(active)

    @property
    def background_color(self) -> tuple[int, int, int]:
        """Pseudônimo/equivalente para clear_color."""
        return self.clear_color

    @background_color.setter
    def background_color(self, val: tuple[int, int, int]) -> None:
        self.clear_color = tuple(val)

    @property
    def active(self) -> bool:
        """Indica se a câmera está ativa e habilitada."""
        return self._active_state and self.enabled

    @active.setter
    def active(self, value: bool) -> None:
        self._active_state = bool(value)

    def start(self) -> None:
        """Registra a câmera no CameraManager."""
        from engine.graphics.camera_manager import CameraManager
        CameraManager.register_camera(self)

    def on_runtime_start(self) -> None:
        """Registra a câmera no CameraManager durante o Play Mode."""
        from engine.graphics.camera_manager import CameraManager
        CameraManager.register_camera(self)

    def destroy(self) -> None:
        """Remove a câmera do CameraManager ao ser destruída."""
        from engine.graphics.camera_manager import CameraManager
        CameraManager.remove_camera(self)
        super().destroy()

    def serialize_properties(self) -> dict[str, Any]:
        """Serializa os parâmetros da câmera."""
        return {
            "zoom": self.zoom,
            "clear_color": list(self.clear_color),
            "viewport_rect": list(self.viewport_rect),
            "priority": self.priority,
            "active": self._active_state
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        """Deserializa os parâmetros da câmera."""
        self.zoom = float(data.get("zoom", self.zoom))
        self.clear_color = tuple(data.get("clear_color", self.clear_color))
        self.viewport_rect = tuple(data.get("viewport_rect", self.viewport_rect))
        self.priority = int(data.get("priority", self.priority))
        self._active_state = bool(data.get("active", self._active_state))

    def world_to_screen(self, world_pos: tuple[float, float] | np.ndarray, screen_width: int, screen_height: int) -> tuple[float, float]:
        """Converte uma coordenada de mundo para pixels na tela com base no zoom e posição da câmera."""
        if not self.game_object:
            return float(world_pos[0]), float(world_pos[1])
        cam_pos = self.game_object.transform.position
        screen_x = (world_pos[0] - cam_pos[0]) * self.zoom + (screen_width * self.viewport_rect[2] / 2.0) + (screen_width * self.viewport_rect[0])
        screen_y = (world_pos[1] - cam_pos[1]) * self.zoom + (screen_height * self.viewport_rect[3] / 2.0) + (screen_height * self.viewport_rect[1])
        return screen_x, screen_y

    def screen_to_world(self, screen_pos: tuple[float, float], screen_width: int, screen_height: int) -> tuple[float, float]:
        """Converte coordenadas de tela de volta para espaço de mundo."""
        if not self.game_object:
            return float(screen_pos[0]), float(screen_pos[1])
        cam_pos = self.game_object.transform.position
        world_x = (screen_pos[0] - (screen_width * self.viewport_rect[0]) - (screen_width * self.viewport_rect[2] / 2.0)) / self.zoom + cam_pos[0]
        world_y = (screen_pos[1] - (screen_height * self.viewport_rect[1]) - (screen_height * self.viewport_rect[3] / 2.0)) / self.zoom + cam_pos[1]
        return world_x, world_y

