"""Scene grid, camera, selection-gizmo and HUD overlays."""
from __future__ import annotations

import math
from typing import Any, Callable


class ViewportOverlayRenderer:
    def __init__(self, pygame: Any) -> None:
        self.pygame = pygame

    def draw_scene(
        self, screen: Any, objects: dict[str, dict[str, Any]], width: int, height: int,
        camera_x: float, camera_y: float, zoom: float,
        world_to_screen: Callable[[float, float], tuple[float, float]],
    ) -> None:
        pg = self.pygame
        spacing = max(8.0, 32.0 * zoom)
        grid_x, grid_y = (-camera_x * zoom) % spacing, (-camera_y * zoom) % spacing
        while grid_x < width:
            pg.draw.line(screen, (45, 48, 59), (int(grid_x), 0), (int(grid_x), height))
            grid_x += spacing
        while grid_y < height:
            pg.draw.line(screen, (45, 48, 59), (0, int(grid_y)), (width, int(grid_y)))
            grid_y += spacing
        origin_x, origin_y = world_to_screen(0.0, 0.0)
        if 0 <= origin_x <= width:
            pg.draw.line(screen, (112, 120, 142), (int(origin_x), 0), (int(origin_x), height), 2)
        if 0 <= origin_y <= height:
            pg.draw.line(screen, (112, 120, 142), (0, int(origin_y)), (width, int(origin_y)), 2)
        for obj in objects.values():
            if self._is_camera(obj):
                camera = obj.get("camera") or {}
                camera_zoom = max(0.1, float(camera.get("zoom", 1.0)))
                camera_width = float(camera.get("width", 800.0)) / camera_zoom
                camera_height = float(camera.get("height", 600.0)) / camera_zoom
                center_x, center_y = world_to_screen(float(obj["x"]), float(obj["y"]))
                rect = pg.Rect(
                    int(center_x - camera_width * zoom / 2), int(center_y - camera_height * zoom / 2),
                    int(camera_width * zoom), int(camera_height * zoom),
                )
                pg.draw.rect(screen, (240, 240, 240), rect, 1)
                color = (255, 100, 100) if camera.get("active", True) else (150, 150, 150)
                pg.draw.rect(screen, color, (int(center_x - 4), int(center_y - 4), 8, 8))
            elif bool(obj.get("editor_locked", False)):
                center_x, center_y = world_to_screen(float(obj["x"]), float(obj["y"]))
                width = float(obj["w"]) * zoom
                height = float(obj["h"]) * zoom
                corner_x = int(center_x - width / 2.0)
                corner_y = int(center_y - height / 2.0)
                self._draw_lock_icon(screen, corner_x, corner_y)

    def draw_selection(
        self, screen: Any, obj: dict[str, Any], active_tool: str,
        object_x: float, object_y: float, object_width: int, object_height: int,
        render_zoom: float, world_to_screen: Callable[[float, float], tuple[float, float]],
    ) -> None:
        pg = self.pygame
        angle = float(obj.get("rotation", 0.0))
        radians = math.radians(angle)
        collider = obj.get("collider") if isinstance(obj.get("collider"), dict) else None
        outline_width = float((collider or {}).get("width", obj["w"]))
        outline_height = float((collider or {}).get("height", obj["h"]))
        offset_x = float((collider or {}).get("offset_x", 0.0))
        offset_y = float((collider or {}).get("offset_y", 0.0))
        rotated_x = offset_x * math.cos(radians) - offset_y * math.sin(radians)
        rotated_y = offset_x * math.sin(radians) + offset_y * math.cos(radians)
        collider_x, collider_y = world_to_screen(obj["x"] + rotated_x, obj["y"] + rotated_y)
        locked = bool(obj.get("editor_locked", False))
        color = (255, 196, 92) if locked else (
            (255, 187, 72) if (collider or {}).get("is_trigger") else (125, 212, 255)
        )
        if (collider or {}).get("type") == "circle":
            radius = max(1, int(float(collider.get("radius", min(obj["w"], obj["h"]) / 2.0)) * render_zoom))
            pg.draw.circle(screen, color, (int(collider_x), int(collider_y)), radius, 2)
            corner_x = int(collider_x - radius)
            corner_y = int(collider_y - radius)
        else:
            surface = pg.Surface((max(1, int(outline_width * render_zoom) + 8), max(1, int(outline_height * render_zoom) + 8)), pg.SRCALPHA)
            pg.draw.rect(surface, color, surface.get_rect().inflate(-6, -6), width=2, border_radius=4)
            rotated = pg.transform.rotate(surface, -angle)
            screen.blit(rotated, rotated.get_rect(center=(int(collider_x), int(collider_y))))
            corner_x = int(collider_x - (outline_width * render_zoom) / 2.0)
            corner_y = int(collider_y - (outline_height * render_zoom) / 2.0)
        if locked:
            self._draw_lock_icon(screen, corner_x, corner_y)
            return

    def _draw_lock_icon(self, screen: Any, x: int, y: int) -> None:
        """Draw a vector padlock icon at screen coordinates (x, y)."""
        pg = self.pygame
        bg_rect = pg.Rect(x - 4, y - 18, 22, 22)
        pg.draw.rect(screen, (15, 18, 26), bg_rect, border_radius=4)
        pg.draw.rect(screen, (255, 196, 92), bg_rect, width=1, border_radius=4)

        shackle_rect = pg.Rect(x + 2, y - 14, 10, 9)
        pg.draw.rect(screen, (255, 196, 92), shackle_rect, width=2, border_top_left_radius=4, border_top_right_radius=4)

        body_rect = pg.Rect(x, y - 7, 14, 10)
        pg.draw.rect(screen, (255, 196, 92), body_rect, border_radius=2)

        pg.draw.circle(screen, (20, 24, 35), (x + 7, y - 2), 2)
        if active_tool == "move":
            self._draw_move(screen, object_x, object_y, radians)
        elif active_tool == "rotate":
            radius = int(max(object_width, object_height) / 2 + 20)
            pg.draw.circle(screen, (245, 194, 78), (int(object_x), int(object_y)), radius, 2)
            end = (int(object_x + math.cos(radians) * radius), int(object_y + math.sin(radians) * radius))
            pg.draw.line(screen, (255, 235, 150), (int(object_x), int(object_y)), end, 1)
        elif active_tool == "scale":
            self._draw_scale(screen, obj, object_x, object_y, radians, render_zoom)

    def _draw_move(self, screen: Any, x: float, y: float, radians: float) -> None:
        pg = self.pygame
        direction_x = (math.cos(radians), math.sin(radians))
        direction_y = (-math.sin(radians), math.cos(radians))
        end_x = (int(x + direction_x[0] * 92), int(y + direction_x[1] * 92))
        end_y = (int(x - direction_y[0] * 92), int(y - direction_y[1] * 92))
        pg.draw.line(screen, (245, 78, 78), (int(x), int(y)), end_x, 4)
        pg.draw.line(screen, (82, 211, 106), (int(x), int(y)), end_y, 4)
        for endpoint, direction, color in ((end_x, direction_x, (245, 78, 78)), (end_y, (-direction_y[0], -direction_y[1]), (82, 211, 106))):
            vector = pg.Vector2(direction)
            point = pg.Vector2(endpoint)
            pg.draw.polygon(screen, color, [point, point - vector * 12 + pg.Vector2(-vector.y, vector.x) * 6, point - vector * 12 - pg.Vector2(-vector.y, vector.x) * 6])

    def _draw_scale(self, screen: Any, obj: dict[str, Any], x: float, y: float, radians: float, zoom: float) -> None:
        pg = self.pygame
        half_w, half_h = float(obj["w"]) * zoom / 2.0, float(obj["h"]) * zoom / 2.0
        local = [(-half_w, -half_h), (0.0, -half_h), (half_w, -half_h), (half_w, 0.0),
                 (half_w, half_h), (0.0, half_h), (-half_w, half_h), (-half_w, 0.0)]
        handles = [(int(x + hx * math.cos(radians) - hy * math.sin(radians)), int(y + hx * math.sin(radians) + hy * math.cos(radians))) for hx, hy in local]
        for start, end in ((0, 2), (2, 4), (4, 6), (6, 0)):
            pg.draw.line(screen, (125, 212, 255), handles[start], handles[end], 1)
        for point in handles:
            surface = pg.Surface((8, 8), pg.SRCALPHA)
            surface.fill((125, 212, 255))
            rotated = pg.transform.rotate(surface, -math.degrees(radians))
            screen.blit(rotated, rotated.get_rect(center=point))

    def draw_hud(self, screen: Any, hud_entries: Any, width: int, height: int) -> None:
        pg = self.pygame
        for position, entries in hud_entries.grouped().items():
            for index, entry in enumerate(entries):
                font = pg.font.Font(None, max(12, min(72, int(entry.get("font_size", 22)))))
                text = font.render(str(entry.get("text", "")), True, tuple(entry.get("color", (255, 255, 255)))[:3])
                panel = pg.Surface((text.get_width() + 20, text.get_height() + 10), pg.SRCALPHA)
                panel.fill((10, 14, 24, 185))
                panel.blit(text, (10, 5))
                margin, gap = 14, 6
                if position == "top-right":
                    point = (width - panel.get_width() - margin, margin + index * (panel.get_height() + gap))
                elif position == "center":
                    point = ((width - panel.get_width()) // 2, (height - panel.get_height()) // 2 + index * (panel.get_height() + gap))
                elif position == "bottom-left":
                    point = (margin, height - margin - (index + 1) * (panel.get_height() + gap))
                elif position == "bottom-right":
                    point = (width - panel.get_width() - margin, height - margin - (index + 1) * (panel.get_height() + gap))
                else:
                    point = (margin, margin + index * (panel.get_height() + gap))
                screen.blit(panel, point)

    @staticmethod
    def _is_camera(obj: dict[str, Any]) -> bool:
        return "Camera2D" in obj.get("component_names", []) or isinstance(obj.get("camera"), dict) or obj.get("mesh_type") == "Camera"
