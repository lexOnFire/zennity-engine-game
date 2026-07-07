from __future__ import annotations

from pathlib import Path
from typing import Any

import pygame

from engine.core.component import Component


class UIElement(Component):
    """Base oficial para componentes de UI em Runtime Screen Space."""

    component_type = "UIElement"

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        width: float = 100.0,
        height: float = 30.0,
        visible: bool = True,
        z_order: int = 0,
    ) -> None:
        super().__init__()
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.visible = bool(visible)
        self.z_order = int(z_order)

    def on_runtime_start(self) -> None:
        """Isola objetos puramente UI do world draw sem esconder objetos mistos."""
        if self.game_object is None:
            return None
        if self._owner_is_pure_ui():
            self.game_object.runtime_hidden = True
        elif hasattr(self.game_object, "runtime_hidden"):
            delattr(self.game_object, "runtime_hidden")
        return None

    def _owner_is_pure_ui(self) -> bool:
        if self.game_object is None:
            return False
        for component in getattr(self.game_object, "components", []):
            if component is self or isinstance(component, UIElement):
                continue
            if getattr(component, "required", False) or getattr(component, "type_name", "") == "Transform":
                continue
            return False
        return True

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "x": float(self.x),
            "y": float(self.y),
            "width": float(self.width),
            "height": float(self.height),
            "visible": bool(self.visible),
            "z_order": int(self.z_order),
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.x = float(data.get("x", self.x))
        self.y = float(data.get("y", self.y))
        self.width = float(data.get("width", self.width))
        self.height = float(data.get("height", self.height))
        self.visible = bool(data.get("visible", self.visible))
        self.z_order = int(data.get("z_order", self.z_order))


class Canvas(UIElement):
    """Agrupa elementos de UI e define a ordem de renderizacao do HUD."""

    component_type = "Canvas"
    unique = True

    def __init__(self, visible: bool = True, z_order: int = 0) -> None:
        super().__init__(x=0.0, y=0.0, width=0.0, height=0.0, visible=visible, z_order=z_order)


class LabelComponent(UIElement):
    component_type = "Label"

    def __init__(
        self,
        text: str = "Label",
        x: float = 0.0,
        y: float = 0.0,
        font_size: int = 20,
        color: tuple[int, int, int] = (255, 255, 255),
        visible: bool = True,
        z_order: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=0.0, height=0.0, visible=visible, z_order=z_order)
        self.text = str(text)
        self.font_size = int(font_size)
        self.color = tuple(color)

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({"text": self.text, "font_size": int(self.font_size), "color": list(self.color)})
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.text = str(data.get("text", self.text))
        self.font_size = int(data.get("font_size", self.font_size))
        self.color = tuple(data.get("color", self.color))


class ImageComponent(UIElement):
    component_type = "Image"
    _surface_cache: dict[str, pygame.Surface] = {}

    def __init__(
        self,
        sprite_path: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 64.0,
        height: float = 64.0,
        color: tuple[int, int, int] = (255, 255, 255),
        alpha: int = 255,
        visible: bool = True,
        z_order: int = 0,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, visible=visible, z_order=z_order)
        self.sprite_path = str(sprite_path)
        self.color = tuple(color)
        self.alpha = int(alpha)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible or self._owner_is_pure_ui():
            return
        surface = self.load_surface(self.sprite_path)
        if surface is None or self.game_object is None:
            return
        transform = self.game_object.transform
        width = max(1, int(abs(float(transform.scale[0]))))
        height = max(1, int(abs(float(transform.scale[1]))))
        if surface.get_size() != (width, height):
            surface = pygame.transform.scale(surface, (width, height))
        if self.alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, int(self.alpha))))
        world_pos = transform.get_world_position()
        x, y = float(world_pos[0]), float(world_pos[1])
        rect = surface.get_rect(center=(int(x), int(y)))
        screen.blit(surface, rect.topleft)

    @classmethod
    def load_surface(cls, sprite_path: str) -> pygame.Surface | None:
        if not sprite_path:
            return None
        resolved = Path(sprite_path)
        if not resolved.is_absolute():
            resolved = Path.cwd() / resolved
        key = str(resolved.resolve())
        if key in cls._surface_cache:
            return cls._surface_cache[key]
        if not resolved.exists():
            return None
        try:
            surface = pygame.image.load(str(resolved)).convert_alpha()
        except Exception:
            return None
        cls._surface_cache[key] = surface
        return surface

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({"sprite_path": self.sprite_path, "color": list(self.color), "alpha": int(self.alpha)})
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.sprite_path = str(data.get("sprite_path", self.sprite_path))
        self.color = tuple(data.get("color", self.color))
        self.alpha = int(data.get("alpha", self.alpha))


class ButtonComponent(UIElement):
    component_type = "Button"

    def __init__(
        self,
        text: str = "Button",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 140.0,
        height: float = 38.0,
        visible: bool = True,
        z_order: int = 0,
        interactable: bool = True,
    ) -> None:
        super().__init__(x=x, y=y, width=width, height=height, visible=visible, z_order=z_order)
        self.text = str(text)
        self.interactable = bool(interactable)

    def serialize_properties(self) -> dict[str, Any]:
        data = super().serialize_properties()
        data.update({"text": self.text, "interactable": bool(self.interactable)})
        return data

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        super().deserialize_properties(data)
        self.text = str(data.get("text", self.text))
        self.interactable = bool(data.get("interactable", self.interactable))


from engine.core.component_registry import register_component

register_component(Canvas)
register_component(LabelComponent)
register_component(LabelComponent, "UILabel")
register_component(ImageComponent)
register_component(ImageComponent, "UIImage")
register_component(ButtonComponent)
register_component(ButtonComponent, "UIButton")
