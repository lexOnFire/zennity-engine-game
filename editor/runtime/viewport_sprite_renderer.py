"""Sprite and animation-frame rendering for the isolated viewport."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

try:
    from engine.graphics.material_graph import MaterialGraph, load_material_graph
except ModuleNotFoundError:
    MaterialGraph = None
    load_material_graph = None


def _safe_color(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    """Accept editor hex colors and sanitize legacy runtime snapshots."""
    if isinstance(value, str):
        raw = value.strip().lstrip("#")
        if len(raw) in {6, 8}:
            try:
                return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4))
            except ValueError:
                pass
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(max(0, min(255, int(channel))) for channel in value[:3])
        except (TypeError, ValueError):
            pass
    return fallback


try:
    from editor.runtime.viewport_render_order import LAYER_ORDER, sort_objects_for_rendering
except ModuleNotFoundError:
    from .viewport_render_order import LAYER_ORDER, sort_objects_for_rendering


class ViewportSpriteRenderer:
    LAYER_ORDER = LAYER_ORDER

    def __init__(self, pygame: Any, prepare_sprite: Callable[..., Any], prepare_scrolling: Callable[..., Any]) -> None:
        self.pygame = pygame
        self.prepare_sprite = prepare_sprite
        self.prepare_scrolling = prepare_scrolling
        self.texture_cache: dict[str, tuple[float, Any]] = {}
        self.material_cache: dict[str, tuple[float, dict[str, Any]]] = {}

    def draw(
        self, screen: Any, objects: dict[str, dict[str, Any]], *, view_mode: str,
        selected_name: str | None, active_tool: str, render_zoom: float,
        world_to_screen: Callable[[float, float], tuple[float, float]], overlay_renderer: Any,
    ) -> None:
        ordered = sort_objects_for_rendering(objects)
        for name, obj in ordered:
            if not obj.get("active", True) or not obj.get("renderer_enabled", True):
                continue
            if view_mode == "game" and self._is_camera(obj):
                continue
            if obj.get("is_group", False) and ("x" not in obj or "y" not in obj):
                continue
            object_x, object_y = world_to_screen(float(obj.get("x", 0.0)), float(obj.get("y", 0.0)))
            width = max(1, int(float(obj["w"]) * render_zoom))
            height = max(1, int(float(obj["h"]) * render_zoom))
            surface = self._surface_for(obj, width, height)
            rotated = self.pygame.transform.rotate(surface, -float(obj.get("rotation", 0.0)))
            screen.blit(rotated, rotated.get_rect(center=(int(object_x), int(object_y))))
            if view_mode == "scene" and name == selected_name:
                overlay_renderer.draw_selection(
                    screen, obj, active_tool, object_x, object_y, width, height,
                    render_zoom, world_to_screen,
                )

    def _surface_for(self, obj: dict[str, Any], width: int, height: int) -> Any:
        material = self._material_values(obj)
        render_obj = obj
        if material.get("texture") and not obj.get("texture"):
            render_obj = dict(obj)
            render_obj["texture"] = material["texture"]
        source, _clip = self._source_surface(render_obj)
        color = self._material_color(obj, material)
        if source is not None:
            scroll = obj.get("_texture_scroll")
            if isinstance(scroll, dict):
                return self.prepare_scrolling(
                    source, (width, height), color,
                    offset_x=float(scroll.get("offset_x", 0.0)), offset_y=float(scroll.get("offset_y", 0.0)),
                    repeat_x=bool(scroll.get("repeat_x", False)), repeat_y=bool(scroll.get("repeat_y", True)),
                )
            surface = self.prepare_sprite(source, (width, height), color)
            surface.set_alpha(max(0, min(255, int(float(material.get("alpha", 1.0)) * 255))))
            return surface
        surface = self.pygame.Surface((width, height), self.pygame.SRCALPHA)
        self.pygame.draw.rect(
            surface,
            color,
            surface.get_rect(),
            border_radius=4,
        )
        surface.set_alpha(max(0, min(255, int(float(material.get("alpha", 1.0)) * 255))))
        return surface

    def _material_values(self, obj: dict[str, Any]) -> dict[str, Any]:
        value = str(obj.get("material", "")).strip()
        if not value.lower().endswith(".zmat") or MaterialGraph is None or load_material_graph is None:
            return {}
        path = Path(value)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            modified = path.stat().st_mtime
            cached = self.material_cache.get(str(path))
            if cached is None or cached[0] != modified:
                result = MaterialGraph(load_material_graph(path)).evaluate_cpu()
                cached = (modified, result)
                self.material_cache[str(path)] = cached
            return cached[1]
        except (OSError, ValueError, TypeError):
            return {}

    @staticmethod
    def _material_color(obj: dict[str, Any], material: dict[str, Any]) -> tuple[int, int, int]:
        if not material:
            return _safe_color(obj.get("color"), (255, 255, 255))
        base = material.get("base_color", [1.0, 1.0, 1.0, 1.0])
        glow = material.get("emissive", [0.0, 0.0, 0.0, 1.0])
        if not isinstance(base, (list, tuple)) or not isinstance(glow, (list, tuple)):
            return _safe_color(obj.get("color"), (255, 255, 255))
        return tuple(
            max(0, min(255, int((float(base[index]) + float(glow[index])) * 255)))
            for index in range(3)
        )

    def _source_surface(self, obj: dict[str, Any]) -> tuple[Any | None, dict[str, Any] | None]:
        texture = str(obj.get("texture", "")).strip()
        clip = None
        animator = obj.get("animator")
        if isinstance(animator, dict) and str(obj.get("_current_animation_name", "")) != "Nenhum":
            clips = animator.get("clips")
            if isinstance(clips, dict):
                candidate = clips.get(str(obj.get("_current_animation_name", animator.get("active_clip", ""))))
                if isinstance(candidate, dict) and candidate.get("texture"):
                    clip, texture = candidate, str(candidate["texture"])
        if not texture:
            return None, clip
        path = Path(texture)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            modified = path.stat().st_mtime
            cached = self.texture_cache.get(str(path))
            if cached is None or cached[0] != modified:
                cached = (modified, self.pygame.image.load(str(path)).convert_alpha())
                self.texture_cache[str(path)] = cached
            source = cached[1]
            return self._animation_frame(source, obj, clip), clip
        except (OSError, self.pygame.error):
            return None, clip

    def _animation_frame(self, source: Any, obj: dict[str, Any], clip: dict[str, Any] | None) -> Any:
        if clip is None:
            return source
        frame_width = max(1, int(clip.get("frame_width", source.get_width())))
        frame_height = max(1, int(clip.get("frame_height", source.get_height())))
        columns = max(1, source.get_width() // frame_width)
        offset = int(obj.get("_animation_frame", 0))
        frames = clip.get("frames")
        frame = max(0, int(frames[min(offset, len(frames) - 1)])) if isinstance(frames, list) and frames else max(0, int(clip.get("start_frame", 0))) + offset
        x, y = (frame % columns) * frame_width, (frame // columns) * frame_height
        if x + frame_width <= source.get_width() and y + frame_height <= source.get_height():
            return source.subsurface((x, y, frame_width, frame_height)).copy()
        return source

    @staticmethod
    def _is_camera(obj: dict[str, Any]) -> bool:
        return "Camera2D" in obj.get("component_names", []) or isinstance(obj.get("camera"), dict) or obj.get("mesh_type") == "Camera"
