"""
editor/viewport/viewport_renderer.py
ViewportRenderer coordinates grid, outlines, bounding boxes and HUD overlays.
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
from editor.gizmos.qt_gizmo_overlay import QtMoveGizmoOverlay

class ViewportRenderer:
    """Coordinates all QPainter based Scene View overlays."""

    def __init__(self) -> None:
        self.grid_renderer = GridRenderer()
        self.outline_renderer = SelectionOutlineRenderer()
        self.bounding_box_renderer = BoundingBoxRenderer()
        self.overlay = ViewportOverlay()
        self.move_gizmo = QtMoveGizmoOverlay()
        self._fps_last_time: float = time.time()
        self._fps_value: float = 60.0

    def calculate_fps(self) -> float:
        """Return a smoothed render FPS value."""
        now = time.time()
        delta = now - self._fps_last_time
        self._fps_last_time = now
        if delta > 0.0:
            current_fps = 1.0 / delta
            self._fps_value += (current_fps - self._fps_value) * 0.1
        return self._fps_value

    def render_grid(self, painter: QPainter, camera: ViewportCamera, show_grid: bool) -> None:
        """Draw the editor grid when enabled."""
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
        scene_name: str = "Scene",
        view_mode: str = "Edit",
        overlays_visible: bool = True,
        selection_visible: bool = True,
    ) -> None:
        """Compatibility wrapper for the original combined overlay call."""
        self.render_selection_overlays(
            painter=painter,
            camera=camera,
            selected=selected,
            active_tool_name=active_tool_name,
            is_playing=is_playing,
            selection_visible=selection_visible,
        )
        self.render_hud_overlays(
            painter=painter,
            camera=camera,
            active_tool_name=active_tool_name,
            object_count=object_count,
            grid_size=grid_size,
            snap_on=snap_on,
            mouse_screen_pos=mouse_screen_pos,
            is_playing=is_playing,
            scene_name=scene_name,
            view_mode=view_mode,
            overlays_visible=overlays_visible,
        )

    def render_selection_overlays(
        self,
        painter: QPainter,
        camera: ViewportCamera,
        selected: Any,
        active_tool_name: str,
        is_playing: bool = False,
        selection_visible: bool = True,
    ) -> None:
        """Draw only the selection outline and its bounding box."""
        has_sprite = any(
            getattr(component, "type_name", type(component).__name__) == "Image"
            and bool(str(getattr(component, "sprite_path", "") or "").strip())
            for component in getattr(selected, "components", ())
        ) if selected is not None else False
        if has_sprite and active_tool_name.lower() != "scale":
            selection_visible = False
        if selected is None or is_playing:
            return
            
        if selection_visible:
            self.outline_renderer.draw(painter, selected, camera.world_to_viewport)
            self.bounding_box_renderer.draw(
                painter,
                selected,
                camera.world_to_viewport,
                show_handles=active_tool_name.lower() == "scale",
            )
            
        if active_tool_name.lower() == "move":
            self.move_gizmo.draw(painter, selected, camera.world_to_viewport)

    def render_hud_overlays(
        self,
        painter: QPainter,
        camera: ViewportCamera,
        active_tool_name: str,
        object_count: int,
        grid_size: int,
        snap_on: bool,
        mouse_screen_pos: tuple[float, float],
        is_playing: bool = False,
        scene_name: str = "Scene",
        view_mode: str = "Edit",
        overlays_visible: bool = True,
    ) -> None:
        """Draw only HUD, coordinates and debug information."""
        if not overlays_visible:
            return
        vp_w, vp_h = camera.vp_w, camera.vp_h
        fps = self.calculate_fps()
        camera_name = "Camera 2D"
        self.overlay.draw_hud(
            painter,
            vp_w,
            vp_h,
            camera_name=camera_name,
            fps=fps,
            object_count=object_count,
            active_tool=active_tool_name,
            scene_name=scene_name,
            view_mode=view_mode,
            is_playing=is_playing,
        )

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
