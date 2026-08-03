from __future__ import annotations
from typing import Optional, Tuple
import pygame
from engine.core import Component


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

        # Cache de renderização
        self._cached_source_surface: pygame.Surface | None = None
        self._cached_zoom: float = 1.0
        self._cached_flip_x: bool = False
        self._cached_flip_y: bool = False
        self._cached_color: Tuple[int, int, int] = (255, 255, 255)
        self._cached_alpha: int = 255
        self._cached_final_surface: pygame.Surface | None = None

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

        # BUG FIX: `Camera._active` never existed on the Camera class — this
        # raised AttributeError on every SpriteRenderer.draw() call, which
        # silently aborted the frame (Engine.run() only logs the traceback).
        # Resolve the active camera via the shared helper (Camera as source of
        # truth, Camera2D as legacy fallback, "no camera" as raw world coords).
        from engine.graphics.active_camera import get_active_camera
        cam = get_active_camera()
        zoom = cam.zoom if cam is not None else 1.0
        color = getattr(self, "color", (255, 255, 255))
        alpha = getattr(self, "alpha", 255)

        # Verifica se o cache é válido
        if (
            self._cached_final_surface is None
            or self._cached_source_surface is not self._surface
            or self._cached_zoom != zoom
            or self._cached_flip_x != self.flip_x
            or self._cached_flip_y != self.flip_y
            or self._cached_color != color
            or self._cached_alpha != alpha
        ):
            # Reconstrói a superfície final no cache
            surf = self._surface
            if self.flip_x or self.flip_y:
                surf = pygame.transform.flip(surf, self.flip_x, self.flip_y)

            if zoom != 1.0:
                new_w = max(1, int(self._width * zoom))
                new_h = max(1, int(self._height * zoom))
                surf = pygame.transform.scale(surf, (new_w, new_h))

            from engine.graphics.tint import apply_pygame_tint
            surf = apply_pygame_tint(surf, color, alpha)

            # Atualiza o cache
            self._cached_source_surface = self._surface
            self._cached_zoom = zoom
            self._cached_flip_x = self.flip_x
            self._cached_flip_y = self.flip_y
            self._cached_color = color
            self._cached_alpha = alpha
            self._cached_final_surface = surf
        else:
            surf = self._cached_final_surface

        if cam is not None and cam.game_object is not None:
            # BUG FIX: world_to_screen() requires screen_width/screen_height —
            # the old call site passed only (wx, wy), which raised a
            # TypeError (missing 2 required positional arguments).
            sx, sy = cam.world_to_screen((wx, wy), screen.get_width(), screen.get_height())
            # BUG FIX: world_to_screen() returns numpy float32/float64 scalars
            # (cam_pos comes from a numpy Transform array). pygame-ce's
            # Surface.blit() rejects numpy scalar types as a blit dest with
            # "invalid destination position for blit" — cast to plain
            # Python int, exactly like every other draw call in the engine
            # (TileMap, ParticleSystem, the demos) already does.
            draw_x = int(sx) - surf.get_width() // 2
            draw_y = int(sy) - surf.get_height() // 2
        else:
            draw_x = int(wx) - surf.get_width() // 2
            draw_y = int(wy) - surf.get_height() // 2

        screen.blit(surf, (draw_x, draw_y))
