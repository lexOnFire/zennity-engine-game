from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame


_MAX_SPRITE_CACHE = 256
_MAX_BACKGROUND_CACHE = 64


def _resolved_key(sprite_path: str) -> str:
    if not sprite_path:
        return ""
    path = Path(str(sprite_path))
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        return str(path.resolve())
    except Exception:
        return str(path)


def _trim_cache(cache: dict, limit: int) -> None:
    while len(cache) > limit:
        try:
            cache.pop(next(iter(cache)))
        except Exception:
            return


def _is_screen_rect_visible(x: float, y: float, width: int, height: int, screen: pygame.Surface) -> bool:
    # Rotation can expand the final blit rect, so cull with a conservative radius.
    radius = max(float(width), float(height), 32.0) * 0.75
    return not (
        x + radius < 0
        or x - radius > screen.get_width()
        or y + radius < 0
        or y - radius > screen.get_height()
    )


def apply_sprite_performance_patch(ImageComponent: type, InfiniteBackground: type | None = None) -> bool:
    if getattr(ImageComponent, "_zennity_sprite_perf_patch", False):
        return True

    ImageComponent._transformed_cache = {}

    def transformed_surface(cls, sprite_path: str, width: int, height: int, alpha: int, rz: float):
        base = cls.load_surface(sprite_path)
        if base is None:
            return None
        rz_key = round(float(rz), 1)
        key = (_resolved_key(sprite_path), int(width), int(height), int(alpha), rz_key)
        cached = cls._transformed_cache.get(key)
        if cached is not None:
            return cached
        surface = base
        if surface.get_size() != (int(width), int(height)):
            surface = pygame.transform.smoothscale(surface, (int(width), int(height)))
        if int(alpha) < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, int(alpha))))
        if rz_key != 0.0:
            surface = pygame.transform.rotate(surface, -rz_key)
        cls._transformed_cache[key] = surface
        _trim_cache(cls._transformed_cache, _MAX_SPRITE_CACHE)
        return surface

    def draw(self, screen: pygame.Surface) -> None:
        if not getattr(self, "visible", True) or self._owner_is_pure_ui():
            return
        if self.game_object is None:
            return
        transform = self.game_object.transform
        zoom = 1.0
        world_pos = transform.get_world_position()
        try:
            from engine.graphics.camera import Camera
            from engine.graphics.camera2d import Camera2D
            main_cam = Camera.main
            if main_cam:
                x, y = main_cam.world_to_screen(world_pos, screen.get_width(), screen.get_height())
                zoom = float(getattr(main_cam, "zoom", 1.0))
            elif Camera2D.main:
                x, y = Camera2D.main.world_to_screen(world_pos, screen.get_width(), screen.get_height())
                zoom = float(getattr(Camera2D.main, "zoom", 1.0))
            else:
                x, y = float(world_pos[0]), float(world_pos[1])
        except Exception:
            x, y = float(world_pos[0]), float(world_pos[1])
        width = max(1, int(abs(float(transform.scale[0]) * zoom)))
        height = max(1, int(abs(float(transform.scale[1]) * zoom)))
        if not _is_screen_rect_visible(float(x), float(y), width, height, screen):
            return
        alpha = max(0, min(255, int(getattr(self, "alpha", 255))))
        rz = float(getattr(transform, "rz", 0.0))
        # A cache mantém apenas transformações geométricas; tint é aplicado em
        # uma cópia para não contaminar outros componentes que usam a imagem.
        surface = ImageComponent.transformed_surface(getattr(self, "sprite_path", ""), width, height, 255, rz)
        if surface is None:
            return
        from engine.graphics.tint import apply_pygame_tint
        surface = apply_pygame_tint(surface, getattr(self, "color", (255, 255, 255)), alpha)
        rect = surface.get_rect(center=(int(x), int(y)))
        screen.blit(surface, rect.topleft)

    ImageComponent.transformed_surface = classmethod(transformed_surface)
    ImageComponent.draw = draw
    ImageComponent._zennity_sprite_perf_patch = True

    if InfiniteBackground is not None and not getattr(InfiniteBackground, "_zennity_sprite_perf_patch", False):
        InfiniteBackground._tile_cache = {}

        def background_tile(self, source: pygame.Surface, tw: int, th: int):
            key = (_resolved_key(getattr(self, "sprite_path", "")), int(tw), int(th), int(getattr(self, "alpha", 255)))
            cached = InfiniteBackground._tile_cache.get(key)
            if cached is not None:
                return cached
            surface = source
            if surface.get_size() != (tw, th):
                surface = pygame.transform.smoothscale(surface, (tw, th))
            alpha = max(0, min(255, int(getattr(self, "alpha", 255))))
            if alpha < 255:
                surface = surface.copy()
                surface.set_alpha(alpha)
            InfiniteBackground._tile_cache[key] = surface
            _trim_cache(InfiniteBackground._tile_cache, _MAX_BACKGROUND_CACHE)
            return surface

        def background_draw(self, screen: pygame.Surface) -> None:
            if not getattr(self, "enabled", True) or not getattr(self, "visible", True):
                return
            source = ImageComponent.load_surface(getattr(self, "sprite_path", ""))
            if source is None:
                return
            sw, sh = max(1, int(screen.get_width())), max(1, int(screen.get_height()))
            if getattr(self, "scale_to_screen", True):
                tw, th = sw, sh
            else:
                tw = max(1, int(source.get_width() * float(getattr(self, "tile_scale", 1.0))))
                th = max(1, int(source.get_height() * float(getattr(self, "tile_scale", 1.0))))
            surface = background_tile(self, source, tw, th)
            cam_x = cam_y = 0.0
            if float(getattr(self, "parallax", 0.0)):
                try:
                    from engine.graphics.camera import Camera
                    from engine.graphics.camera2d import Camera2D
                    cam = Camera.main or Camera2D.main
                    if cam is not None and getattr(cam, "transform", None) is not None:
                        cam_x = float(cam.transform.position[0]) * float(getattr(self, "parallax", 0.0))
                        cam_y = float(cam.transform.position[1]) * float(getattr(self, "parallax", 0.0))
                except Exception:
                    pass
            direction = str(getattr(self, "direction", "horizontal")).lower()
            loop_x = direction in ("horizontal", "both", "xy", "x")
            loop_y = direction in ("vertical", "both", "xy", "y")
            ox = (float(getattr(self, "_offset_x", 0.0)) + cam_x) % tw if loop_x else 0.0
            oy = (float(getattr(self, "_offset_y", 0.0)) + cam_y) % th if loop_y else 0.0
            start_x = -int(ox) if loop_x else 0
            start_y = -int(oy) if loop_y else 0
            end_x = sw + (tw if loop_x else 0)
            end_y = sh + (th if loop_y else 0)
            x_values = range(start_x, end_x + 1, tw) if loop_x else range(0, 1)
            y_values = range(start_y, end_y + 1, th) if loop_y else range(0, 1)
            for x in x_values:
                for y in y_values:
                    screen.blit(surface, (x, y))

        InfiniteBackground.draw = background_draw
        InfiniteBackground._zennity_sprite_perf_patch = True
    return True
