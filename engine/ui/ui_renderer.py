from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from engine.ui.runtime_components import ButtonComponent, Canvas, ImageComponent, LabelComponent, UIElement


class UIRenderer:
    """Renderer screen-space independente da câmera da cena."""

    def __init__(self) -> None:
        self._font_cache: dict[tuple[int, bool], pygame.font.Font] = {}
        self._image_cache: dict[str, pygame.Surface] = {}

    def render(self, runtime_scene: Any, screen: pygame.Surface) -> None:
        elements = self._collect_elements(runtime_scene)
        for element in sorted(elements, key=lambda item: int(getattr(item, "z_order", 0))):
            if not bool(getattr(element, "visible", True)):
                continue
            if isinstance(element, LabelComponent):
                self._draw_label(element, screen)
            elif isinstance(element, ImageComponent):
                self._draw_image(element, screen)
            elif isinstance(element, ButtonComponent):
                self._draw_button(element, screen)

    def _collect_elements(self, runtime_scene: Any) -> list[UIElement]:
        components: list[UIElement] = []
        has_canvas = False
        objs = getattr(runtime_scene, "editable_objects", getattr(runtime_scene, "game_objects", []))
        for obj in list(objs):
            for component in getattr(obj, "components", []):
                if isinstance(component, Canvas):
                    has_canvas = True
                elif isinstance(component, UIElement):
                    components.append(component)
        return components if has_canvas else []

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (max(1, int(size)), bool(bold))
        if key not in self._font_cache:
            self._font_cache[key] = pygame.font.SysFont("sans", key[0], bold=key[1])
        return self._font_cache[key]

    def _draw_label(self, label: LabelComponent, screen: pygame.Surface) -> None:
        font = self._font(label.font_size)
        surface = font.render(str(label.text), True, tuple(label.color))
        screen.blit(surface, (int(label.x), int(label.y)))

    def _draw_image(self, image: ImageComponent, screen: pygame.Surface) -> None:
        rect = pygame.Rect(int(image.x), int(image.y), max(1, int(image.width)), max(1, int(image.height)))
        surface = self._load_image(image.sprite_path)
        if surface is None:
            placeholder = pygame.Surface(rect.size, pygame.SRCALPHA)
            placeholder.fill((*tuple(image.color[:3]), max(0, min(255, int(image.alpha)))))
            pygame.draw.rect(placeholder, (255, 255, 255, 90), placeholder.get_rect(), 1)
            screen.blit(placeholder, rect.topleft)
            return
        if surface.get_size() != rect.size:
            surface = pygame.transform.scale(surface, rect.size)
        if image.alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, int(image.alpha))))
        screen.blit(surface, rect.topleft)

    def _draw_button(self, button: ButtonComponent, screen: pygame.Surface) -> None:
        rect = pygame.Rect(int(button.x), int(button.y), max(1, int(button.width)), max(1, int(button.height)))
        bg = (60, 80, 120) if button.interactable else (60, 60, 60)
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        pygame.draw.rect(screen, (110, 130, 170), rect, width=1, border_radius=6)
        font = self._font(16, bold=True)
        text = font.render(str(button.text), True, (235, 235, 235))
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

    def _load_image(self, path: str) -> pygame.Surface | None:
        if not path:
            return None
        resolved = Path(path)
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        key = str(resolved)
        if key in self._image_cache:
            return self._image_cache[key]
        if not resolved.exists():
            return None
        try:
            surface = pygame.image.load(str(resolved)).convert_alpha()
        except Exception:
            return None
        self._image_cache[key] = surface
        return surface
