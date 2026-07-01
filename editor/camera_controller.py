"""Controlador de câmera orbital com suavização por lerp."""
from typing import Optional, Tuple
import numpy as np
import pygame
from engine.component import Component


class OrbitCameraController(Component):
    """
    Orbita em torno de um ponto de foco usando botão direito do mouse.
    Suaviza yaw, pitch e distance via lerp para dar sensação de inércia.
    Trava o eixo de órbita automaticamente após 8 px de arrasto.
    """

    def __init__(
        self,
        target: Optional[np.ndarray] = None,
        distance: float = 4.5,
        yaw: float = 0.0,
        pitch: float = 15.0,
    ) -> None:
        super().__init__()
        self.target = target if target is not None else np.array([0.0, 0.0, 1.5], dtype=np.float32)
        self.distance = distance
        self.yaw = yaw
        self.pitch = pitch
        self.is_dragging = False

        self.target_yaw = yaw
        self.target_pitch = pitch
        self.target_distance = distance

        self._last_mouse: Optional[Tuple[int, int]] = None
        self._drag_start: Optional[Tuple[int, int]] = None
        self._orbit_lock: Optional[str] = None  # None | 'h' | 'v'

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        # Suaviza foco em direção ao objeto selecionado
        desired_focus = np.array([0.0, 0.0, 1.5], dtype=np.float32)
        if self.game_object and self.game_object.scene:
            scene = self.game_object.scene
            if 0 <= scene.selected_index < len(scene.editable_objects):
                desired_focus = scene.editable_objects[scene.selected_index].transform.position.copy()
        self.target += (desired_focus - self.target) * 8.0 * dt

        mouse_pos = pygame.mouse.get_pos()
        rmb = pygame.mouse.get_pressed()[2]

        if rmb:
            if self._last_mouse is None:
                # Só inicia arrasto dentro da metade esquerda (Edit View) da viewport
                width = pygame.display.get_surface().get_width()
                right_limit = 230 + (width - 460) // 2
                if 230 <= mouse_pos[0] <= right_limit:
                    self._last_mouse = mouse_pos
                    self._drag_start = mouse_pos
                    self._orbit_lock = None
            else:
                # Detecta travamento de eixo
                if self._orbit_lock is None and self._drag_start is not None:
                    tdx = mouse_pos[0] - self._drag_start[0]
                    tdy = mouse_pos[1] - self._drag_start[1]
                    if np.hypot(tdx, tdy) > 8.0:
                        self._orbit_lock = 'h' if abs(tdx) > abs(tdy) else 'v'

                dx = mouse_pos[0] - self._last_mouse[0]
                dy = mouse_pos[1] - self._last_mouse[1]
                if dx != 0 or dy != 0:
                    if self._orbit_lock in ('h', None):
                        self.target_yaw -= dx * 0.20
                    if self._orbit_lock in ('v', None):
                        self.target_pitch = max(-85.0, min(85.0, self.target_pitch + dy * 0.20))
                    self.is_dragging = True
                self._last_mouse = mouse_pos
        else:
            self._last_mouse = None
            self._drag_start = None
            self._orbit_lock = None
            self.is_dragging = False

        # Lerp suave
        self.yaw      += (self.target_yaw      - self.yaw)      * 12.0 * dt
        self.pitch    += (self.target_pitch    - self.pitch)    * 12.0 * dt
        self.distance += (self.target_distance - self.distance) * 10.0 * dt

        # Posição esférica
        yr = np.radians(self.yaw)
        pr = np.radians(self.pitch)
        ox = -self.distance * np.cos(pr) * np.sin(yr)
        oy =  self.distance * np.sin(pr)
        oz = -self.distance * np.cos(pr) * np.cos(yr)

        self.transform.position = self.target + np.array([ox, oy, oz], dtype=np.float32)
        self.transform.ry = self.yaw
        self.transform.rx = self.pitch
        self.transform.rz = 0.0
