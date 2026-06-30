from __future__ import annotations
from typing import Optional, Tuple
import pygame
from engine.component import Component
from engine.graphics.camera import Camera


class SpriteRenderer(Component):
    """
    Componente que renderiza um sprite (Surface pygame) na posição
    do Transform, respeitando a câmera ativa.

    Uso:
        renderer = SpriteRenderer(surface=my_surface)
        player.add_component(renderer)

        # Ou carregar via AssetManager:
        surf = pygame.image.load("hero.png").convert_alpha()
        player.add_component(SpriteRenderer(surface=surf))
    """

    def __init__(
        self,
        surface: Optional[pygame.Surface] = None,
        color: Tuple[int, int, int] = (255, 255, 255),
        width: int = 32,
        height: int = 32,
        layer: int = 0,           # ordem de renderização (maior = na frente)
        visible: bool = True,
        flip_x: bool = False,
        flip_y: bool = False,
    ) -> None:
        super().__init__()
        self.layer = layer
        self.visible = visible
        self.flip_x = flip_x
        self.flip_y = flip_y

        if surface is not None:
            self._surface = surface
        else:
            # Cria um retângulo colorido como placeholder
            self._surface = pygame.Surface((width, height), pygame.SRCALPHA)
            self._surface.fill(color)

        self._width = self._surface.get_width()
        self._height = self._surface.get_height()

    # ------------------------------------------------------------------
    # Surface
    # ------------------------------------------------------------------

    @property
    def surface(self) -> pygame.Surface:
        return self._surface

    @surface.setter
    def surface(self, new_surface: pygame.Surface) -> None:
        self._surface = new_surface
        self._width = new_surface.get_width()
        self._height = new_surface.get_height()

    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Preenche o surface atual com uma cor sólida."""
        self._surface.fill(color)

    # ------------------------------------------------------------------
    # Renderização
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible or self.game_object is None:
            return

        world_pos = self.game_object.transform.get_world_position()
        wx, wy = float(world_pos[0]), float(world_pos[1])

        # Aplica flip se necessário
        surf = self._surface
        if self.flip_x or self.flip_y:
            surf = pygame.transform.flip(surf, self.flip_x, self.flip_y)

        # Aplica zoom da câmera se existir
        cam = Camera._active
        if cam is not None:
            sx, sy = cam.world_to_screen(wx, wy)
            zoom = cam.zoom
            if zoom != 1.0:
                new_w = max(1, int(self._width * zoom))
                new_h = max(1, int(self._height * zoom))
                surf = pygame.transform.scale(surf, (new_w, new_h))
            # Centraliza o sprite na posição
            draw_x = sx - surf.get_width() // 2
            draw_y = sy - surf.get_height() // 2
        else:
            # Sem câmera: renderiza em coordenadas de mundo direto
            draw_x = int(wx) - self._width // 2
            draw_y = int(wy) - self._height // 2

        screen.blit(surf, (draw_x, draw_y))
