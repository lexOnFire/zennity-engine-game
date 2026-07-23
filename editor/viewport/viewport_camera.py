"""
editor/viewport/viewport_camera.py
─────────────────────────────────────────────────────────────────────────────
Controle de câmera da Viewport, gerenciando Pan, Zoom suave, zoom direcionado
ao cursor e conversão de coordenadas (World <-> Viewport/Screen).
"""
from __future__ import annotations

import numpy as np


class ViewportCamera:
    """Controle de Câmera da Viewport 2D/3D (Zennity Editor).

    Gerencia o zoom suave, pan e mapeamento de coordenadas bidirecional.
    """

    def __init__(self) -> None:
        self.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.zoom: float = 1.0
        self.target_zoom: float = 1.0

        # Para o zoom-to-mouse suave: (anchor_screen, anchor_world)
        self.zoom_anchor: tuple[tuple[float, float], np.ndarray] | None = None

        self.vp_w: int = 800
        self.vp_h: int = 600

        self.min_zoom: float = 0.05
        self.max_zoom: float = 20.0
        self.zoom_speed: float = 15.0  # Fator de interpolação

    def set_viewport_size(self, w: int, h: int) -> None:
        """Atualiza a dimensão da viewport."""
        self.vp_w = max(32, w)
        self.vp_h = max(32, h)

    def pan(self, dx_px: float, dy_px: float) -> None:
        """Desloca a câmera baseado no arraste do mouse (em pixels).

        O movimento no mundo é proporcional ao zoom.
        """
        self.position[0] -= dx_px / self.zoom
        self.position[1] -= dy_px / self.zoom
        self._sync_to_engine()

    def zoom_to_mouse(self, factor: float, mouse_x: float, mouse_y: float) -> None:
        """Define o novo target de zoom suave direcionado à posição do mouse."""
        old_target = self.target_zoom
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, self.target_zoom * factor))

        # Guarda o ponto âncora antes da interpolação começar.
        # Ângulo e posição de mundo fixos ajudam a reposicionar a câmera no update().
        anchor_screen = (mouse_x, mouse_y)
        anchor_world = self.screen_to_world(anchor_screen)
        self.zoom_anchor = (anchor_screen, anchor_world)

    def update(self, dt: float) -> None:
        """Interpola suavemente o zoom em direção ao target."""
        if abs(self.target_zoom - self.zoom) > 0.001:
            self.zoom += (self.target_zoom - self.zoom) * min(1.0, dt * self.zoom_speed)
            
            # Reposiciona a câmera para manter a âncora de mundo sob o cursor de tela
            if self.zoom_anchor is not None:
                anchor_screen, anchor_world = self.zoom_anchor
                self.position[0] = anchor_world[0] - (anchor_screen[0] - self.vp_w / 2.0) / self.zoom
                self.position[1] = anchor_world[1] - (anchor_screen[1] - self.vp_h / 2.0) / self.zoom
            self._sync_to_engine()
        else:
            self.zoom = self.target_zoom
            if self.zoom_anchor is not None:
                anchor_screen, anchor_world = self.zoom_anchor
                self.position[0] = anchor_world[0] - (anchor_screen[0] - self.vp_w / 2.0) / self.zoom
                self.position[1] = anchor_world[1] - (anchor_screen[1] - self.vp_h / 2.0) / self.zoom
                self.zoom_anchor = None
            self._sync_to_engine()

    def _sync_to_engine(self) -> None:
        """Sincroniza o estado desta câmera com Camera2D.main da engine."""
        from engine.graphics.camera2d import Camera2D
        if Camera2D.main is not None:
            Camera2D.main.zoom = self.zoom
            Camera2D.main.transform.position[0] = self.position[0]
            Camera2D.main.transform.position[1] = self.position[1]

    # ── Conversão de Coordenadas ──────────────────────────────────────────────

    def world_to_screen(self, world_pos: tuple[float, float] | np.ndarray) -> tuple[float, float]:
        """Mapeia coordenadas do espaço mundo [x, y] para tela [px, py]."""
        screen_x = (world_pos[0] - self.position[0]) * self.zoom + (self.vp_w / 2.0)
        screen_y = (world_pos[1] - self.position[1]) * self.zoom + (self.vp_h / 2.0)
        return float(screen_x), float(screen_y)

    def screen_to_world(self, screen_pos: tuple[float, float]) -> np.ndarray:
        """Mapeia coordenadas de tela [px, py] de volta para o espaço mundo."""
        world_x = (screen_pos[0] - (self.vp_w / 2.0)) / self.zoom + self.position[0]
        world_y = (screen_pos[1] - (self.vp_h / 2.0)) / self.zoom + self.position[1]
        return np.array([world_x, world_y, 0.0], dtype=np.float32)

    # Aliases solicitados para a Viewport API
    world_to_viewport = world_to_screen
    viewport_to_world = screen_to_world
