from __future__ import annotations

from typing import Any

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
        """Mantem o GameObject intacto quando a UI entra em Runtime.

        A versao anterior marcava ``game_object.runtime_hidden = True``. Isso
        fazia objetos como Player sumirem ao apertar Play depois de adicionar
        componentes de UI como Button, Label ou Image. Componentes de UI devem
        controlar apenas a propria renderizacao de tela, nao esconder ou mutar
        o GameObject dono.
        """
        return None

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
