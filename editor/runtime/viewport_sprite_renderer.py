"""Sprite and animation-frame rendering for the isolated viewport."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


class ViewportSpriteRenderer:
    LAYER_ORDER = {"Background": 0, "Default": 1, "Foreground": 2, "UI": 3}

    def __init__(self, pygame: Any, prepare_sprite: Callable[..., Any], prepare_scrolling: Callable[..., Any]) -> None:
        self.pygame = pygame
        self.prepare_sprite = prepare_sprite
        self.prepare_scrolling = prepare_scrolling
        self.texture_cache: dict[str, tuple[float, Any]] = {}

    def draw(
        self, screen: Any, objects: dict[str, dict[str, Any]], *, view_mode: str,
        selected_name: str | None, active_tool: str, render_zoom: float,
        world_to_screen: Callable[[float, float], tuple[float, float]], overlay_renderer: Any,
    ) -> None:
        ordered = sorted(objects.items(), key=lambda item: (
            self.LAYER_ORDER.get(str(item[1].get("render_layer", "Default")), 1),
            int(item[1].get("sort_order", 0)),
        ))
        for name, obj in ordered:
            if not obj.get("active", True) or not obj.get("renderer_enabled", True):
                continue
            if view_mode == "game" and self._is_camera(obj):
                continue
            object_x, object_y = world_to_screen(float(obj["x"]), float(obj["y"]))
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
        source, _clip = self._source_surface(obj)
        if source is not None:
            scroll = obj.get("_texture_scroll")
            if isinstance(scroll, dict):
                return self.prepare_scrolling(
                    source, (width, height), obj.get("color", (255, 255, 255)),
                    offset_x=float(scroll.get("offset_x", 0.0)), offset_y=float(scroll.get("offset_y", 0.0)),
                    repeat_x=bool(scroll.get("repeat_x", False)), repeat_y=bool(scroll.get("repeat_y", True)),
                )
            return self.prepare_sprite(source, (width, height), obj.get("color", (255, 255, 255)))
        surface = self.pygame.Surface((width, height), self.pygame.SRCALPHA)
        self.pygame.draw.rect(surface, tuple(obj.get("color", (180, 180, 180))), surface.get_rect(), border_radius=4)
        return surface

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
