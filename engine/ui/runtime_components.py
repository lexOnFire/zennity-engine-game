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
        scene = getattr(self.game_object, "scene", None)
        modern_ids = getattr(scene, "_zennity_modern_sprite_component_ids", ())
        if id(self) in modern_ids:
            return
        surface = self.load_surface(self.sprite_path)
        if surface is None or self.game_object is None:
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
        if surface.get_size() != (width, height):
            surface = pygame.transform.scale(surface, (width, height))
        if self.alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, int(self.alpha))))
        rz = getattr(transform, "rz", 0.0)
        if rz != 0.0:
            surface = pygame.transform.rotate(surface, -rz)
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
            loaded = pygame.image.load(str(resolved))
            surface = loaded.convert_alpha() if pygame.display.get_surface() is not None else loaded.copy()
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


class InfiniteBackground(Component):
    """Fundo infinito/tileable para jogos 2D, ideal para céu espacial em movimento."""

    component_type = "InfiniteBackground"
    unique = True

    def __init__(
        self,
        sprite_path: str = "",
        speed_x: float = 40.0,
        speed_y: float = 0.0,
        direction: str = "horizontal",
        parallax: float = 0.0,
        tile_scale: float = 1.0,
        alpha: int = 255,
        visible: bool = True,
        scale_to_screen: bool = True,
    ) -> None:
        super().__init__()
        self.sprite_path = str(sprite_path)
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.direction = str(direction or "horizontal").lower()
        self.parallax = float(parallax)
        self.tile_scale = max(0.01, float(tile_scale))
        self.alpha = int(alpha)
        self.visible = bool(visible)
        self.scale_to_screen = bool(scale_to_screen)
        self._offset_x = 0.0
        self._offset_y = 0.0

    def update(self, dt: float) -> None:
        if not self.enabled or not self.visible:
            return
        self._offset_x = (self._offset_x + float(self.speed_x) * float(dt)) % 100000.0
        self._offset_y = (self._offset_y + float(self.speed_y) * float(dt)) % 100000.0

    def on_runtime_update(self, delta_time: float) -> None:
        self.update(delta_time)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.enabled or not self.visible:
            return
        surface = ImageComponent.load_surface(self.sprite_path)
        if surface is None:
            return
        sw, sh = max(1, int(screen.get_width())), max(1, int(screen.get_height()))
        if self.scale_to_screen:
            tw, th = sw, sh
        else:
            tw = max(1, int(surface.get_width() * self.tile_scale))
            th = max(1, int(surface.get_height() * self.tile_scale))
        if surface.get_size() != (tw, th):
            surface = pygame.transform.scale(surface, (tw, th))
        if self.alpha < 255:
            surface = surface.copy()
            surface.set_alpha(max(0, min(255, int(self.alpha))))

        cam_x = cam_y = 0.0
        if self.parallax:
            try:
                from engine.graphics.camera import Camera
                from engine.graphics.camera2d import Camera2D
                cam = Camera.main or Camera2D.main
                if cam is not None and getattr(cam, "transform", None) is not None:
                    cam_x = float(cam.transform.position[0]) * self.parallax
                    cam_y = float(cam.transform.position[1]) * self.parallax
            except Exception:
                pass

        direction = self.direction.lower()
        loop_x = direction in ("horizontal", "both", "xy", "x")
        loop_y = direction in ("vertical", "both", "xy", "y")
        ox = (self._offset_x + cam_x) % tw if loop_x else 0.0
        oy = (self._offset_y + cam_y) % th if loop_y else 0.0
        start_x = -int(ox) if loop_x else 0
        start_y = -int(oy) if loop_y else 0
        end_x = sw + (tw if loop_x else 0)
        end_y = sh + (th if loop_y else 0)
        x_values = range(start_x, end_x + 1, tw) if loop_x else range(0, 1)
        y_values = range(start_y, end_y + 1, th) if loop_y else range(0, 1)
        for x in x_values:
            for y in y_values:
                screen.blit(surface, (x, y))

    def serialize_properties(self) -> dict[str, Any]:
        return {
            "sprite_path": self.sprite_path,
            "speed_x": float(self.speed_x),
            "speed_y": float(self.speed_y),
            "direction": self.direction,
            "parallax": float(self.parallax),
            "tile_scale": float(self.tile_scale),
            "alpha": int(self.alpha),
            "visible": bool(self.visible),
            "scale_to_screen": bool(self.scale_to_screen),
        }

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.sprite_path = str(data.get("sprite_path", self.sprite_path))
        self.speed_x = float(data.get("speed_x", self.speed_x))
        self.speed_y = float(data.get("speed_y", self.speed_y))
        self.direction = str(data.get("direction", self.direction)).lower()
        self.parallax = float(data.get("parallax", self.parallax))
        self.tile_scale = max(0.01, float(data.get("tile_scale", self.tile_scale)))
        self.alpha = int(data.get("alpha", self.alpha))
        self.visible = bool(data.get("visible", self.visible))
        self.scale_to_screen = bool(data.get("scale_to_screen", self.scale_to_screen))


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


from engine.ui.sprite_performance_patch import apply_sprite_performance_patch
apply_sprite_performance_patch(ImageComponent, InfiniteBackground)

from engine.core.component_registry import register_component

register_component(Canvas)
register_component(LabelComponent)
register_component(LabelComponent, "UILabel")
register_component(ImageComponent)
register_component(ImageComponent, "UIImage")
register_component(InfiniteBackground)
register_component(InfiniteBackground, "Infinite Background")
register_component(ButtonComponent)
register_component(ButtonComponent, "UIButton")
