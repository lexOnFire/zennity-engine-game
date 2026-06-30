from __future__ import annotations
from typing import Optional, TYPE_CHECKING
import pygame
from engine.component import Component

if TYPE_CHECKING:
    from engine.game_object import GameObject


class Camera(Component):
    """
    Câmera 2D que pode seguir um target suavemente (lerp).

    Uso:
        camera = Camera(screen_width=800, screen_height=600)
        camera_obj = GameObject("Camera")
        camera_obj.add_component(camera)

        # Seguir o player
        camera.set_target(player)

        # Converter posição de mundo para tela
        screen_pos = camera.world_to_screen(world_x, world_y)
    """

    # Câmera ativa global — acessada pelo SpriteRenderer
    _active: Optional["Camera"] = None

    def __init__(
        self,
        screen_width: int = 800,
        screen_height: int = 600,
        zoom: float = 1.0,
        follow_speed: float = 5.0,   # suavidade do follow (lerp factor)
    ) -> None:
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom = zoom
        self.follow_speed = follow_speed

        self._target: Optional["GameObject"] = None
        # Posição interna da câmera no espaço de mundo
        self._pos_x: float = 0.0
        self._pos_y: float = 0.0

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def start(self) -> None:
        Camera._active = self

    def destroy(self) -> None:
        if Camera._active is self:
            Camera._active = None

    # ------------------------------------------------------------------
    # Target / follow
    # ------------------------------------------------------------------

    def set_target(self, target: "GameObject") -> None:
        """Define o GameObject que a câmera vai seguir."""
        self._target = target
        # Snap imediato na primeira atribuição
        if target:
            self._pos_x = target.transform.x
            self._pos_y = target.transform.y

    def update(self, dt: float) -> None:
        """Suaviza o movimento da câmera em direção ao target."""
        if self._target is None:
            return
        tx = self._target.transform.get_world_position()[0]
        ty = self._target.transform.get_world_position()[1]
        # Lerp: move em direção ao target a cada frame
        t = min(self.follow_speed * dt, 1.0)
        self._pos_x += (tx - self._pos_x) * t
        self._pos_y += (ty - self._pos_y) * t

    # ------------------------------------------------------------------
    # Conversão de coordenadas
    # ------------------------------------------------------------------

    def world_to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Converte uma posição de mundo para posição na tela."""
        half_w = self.screen_width / 2
        half_h = self.screen_height / 2
        sx = int((world_x - self._pos_x) * self.zoom + half_w)
        sy = int((world_y - self._pos_y) * self.zoom + half_h)
        return sx, sy

    def screen_to_world(self, screen_x: int, screen_y: int) -> tuple[float, float]:
        """Converte uma posição de tela para posição no mundo."""
        half_w = self.screen_width / 2
        half_h = self.screen_height / 2
        wx = (screen_x - half_w) / self.zoom + self._pos_x
        wy = (screen_y - half_h) / self.zoom + self._pos_y
        return wx, wy

    @property
    def offset(self) -> tuple[int, int]:
        """Offset de renderização usado pelo SpriteRenderer."""
        return (
            int(self._pos_x - self.screen_width  / (2 * self.zoom)),
            int(self._pos_y - self.screen_height / (2 * self.zoom)),
        )
