"""
editor/viewport/viewport_renderer.py
─────────────────────────────────────────────────────────────────────────────
Orquestrador de renderização (ViewportRenderer) coordenando a exibição de grid,
outlines, bounding boxes e HUD overlays usando QPainter.
"""
from __future__ import annotations

import time
from typing import Any
from PySide6.QtGui import QPainter

from editor.viewport.grid_renderer import GridRenderer
from editor.viewport.selection_outline import SelectionOutlineRenderer
from editor.viewport.bounding_box import BoundingBoxRenderer
from editor.viewport.viewport_overlay import ViewportOverlay
from editor.viewport.viewport_camera import ViewportCamera


class ViewportRenderer:
    """Orquestra e gerencia o pipeline de renderização visual da viewport.

    Desenha todos os overlays da viewport (incluindo o grid infinito) utilizando QPainter.
    """

    def __init__(self) -> None:
        self.grid_renderer = GridRenderer()
        self.outline_renderer = SelectionOutlineRenderer()
        self.bounding_box_renderer = BoundingBoxRenderer()
        self.overlay = ViewportOverlay()

        # Para cálculo dinâmico de FPS
        self._fps_last_time: float = time.time()
        self._fps_value: float = 60.0

    def calculate_fps(self) -> float:
        """Calcula e retorna o frame rate atual de renderização."""
        now = time.time()
        delta = now - self._fps_last_time
        self._fps_last_time = now

        # Filtro passa-baixa simples para suavizar o indicador de FPS
        if delta > 0.0:
            current_fps = 1.0 / delta
            self._fps_value += (current_fps - self._fps_value) * 0.1
        return self._fps_value

    def render_grid(self, painter: QPainter, camera: ViewportCamera, show_grid: bool) -> None:
        """Desenha a grade de fundo na Viewport utilizando QPainter (alinhado aos eixos)."""
        if show_grid:
            self.grid_renderer.draw(
                painter=painter,
                vp_w=camera.vp_w,
                vp_h=camera.vp_h,
                zoom=camera.zoom,
                camera_pos=camera.position,
                world_to_viewport=camera.world_to_viewport,
            )

    def render_qt_overlays(
        self,
        painter: QPainter,
        camera: ViewportCamera,
        selected: Any,
        active_tool_name: str,
        object_count: int,
        grid_size: int,
        snap_on: bool,
        mouse_screen_pos: tuple[float, float],
        is_playing: bool = False,
    ) -> None:
        """Renderiza os elementos Qt por cima do framebuffer do Pygame."""
        vp_w, vp_h = camera.vp_w, camera.vp_h

        # 1. Borda de Seleção (Selection Outline)
        if selected is not None and not is_playing:
            self.outline_renderer.draw(painter, selected, camera.world_to_viewport)

        # 2. Caixa Delimitadora.
        # Os handles são exclusivos da Scale Tool para não poluir Move/Rotate.
        if selected is not None and not is_playing:
            show_scale_handles = active_tool_name.lower() == "scale"
            self.bounding_box_renderer.draw(
                painter,
                selected,
                camera.world_to_viewport,
                show_handles=show_scale_handles,
            )

        # 3. HUD Superior Esquerdo (Estatísticas)
        fps = self.calculate_fps()
        camera_name = "Câmera 2D"  # Para Fase 2, padrão 2D
        self.overlay.draw_hud(
            painter,
            vp_w,
            vp_h,
            camera_name=camera_name,
            fps=fps,
            object_count=object_count,
            active_tool=active_tool_name,
        )

        # 4. HUD Inferior Esquerdo (Coordenadas do Mouse e Status)
        mouse_world = camera.screen_to_world(mouse_screen_pos)
        zoom_pct = int(camera.zoom * 100.0)
        self.overlay.draw_coordinates(
            painter,
            vp_w,
            vp_h,
            mouse_world=(float(mouse_world[0]), float(mouse_world[1])),
            zoom_pct=zoom_pct,
            grid_size=grid_size,
            snap_on=snap_on,
        )
