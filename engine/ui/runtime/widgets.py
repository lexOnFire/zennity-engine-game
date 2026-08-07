"""Hierarquia Runtime de Widgets de UI (UICanvas, UIPanel, UIButton, UILabel, UIImage, UIScrollView, UIInput, UIContainer)."""
from __future__ import annotations
from typing import Any, List, Optional


class UIWidget:
    """Classe base runtime para elementos de interface."""

    def __init__(self, name: str = "UIWidget") -> None:
        self.name = name
        self.x: float = 0.0
        self.y: float = 0.0
        self.width: float = 100.0
        self.height: float = 40.0
        self.visible: bool = True
        self.parent: Optional[UIWidget] = None
        self.children: List[UIWidget] = []

    def add_child(self, child: UIWidget) -> None:
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: UIWidget) -> None:
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def serialize(self) -> dict:
        data = {
            "name": self.name,
            "type": getattr(self, "widget_type", self.__class__.__name__),
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "visible": self.visible,
            "children": [c.serialize() for c in self.children],
        }
        for key in (
            "bg_color", "text", "hover_color", "font_size", "text_color",
            "texture_path", "scroll_y", "placeholder", "layout_mode", "render_mode",
        ):
            if hasattr(self, key):
                data[key] = getattr(self, key)
        return data


class RuntimeUICanvas(UIWidget):
    """Container Raiz de Interface para renderização."""

    def __init__(self, name: str = "Canvas") -> None:
        super().__init__(name)
        self.width = 1920.0
        self.height = 1080.0
        self.render_mode = "Screen Space"

    widget_type = "UICanvas"


class UIPanel(UIWidget):
    """Painel de fundo e agrupamento."""

    def __init__(self, name: str = "Panel") -> None:
        super().__init__(name)
        self.bg_color: str = "#2B2B36"


class UIButton(UIWidget):
    """Botão Interativo."""

    def __init__(self, name: str = "Button") -> None:
        super().__init__(name)
        self.text: str = "Click Me"
        self.hover_color: str = "#3B3B48"


class UILabel(UIWidget):
    """Rótulo de Texto."""

    def __init__(self, name: str = "Label") -> None:
        super().__init__(name)
        self.text: str = "Label Text"
        self.font_size: int = 14
        self.text_color: str = "#FFFFFF"


class RuntimeUIImage(UIWidget):
    """Exibição de Imagem ou Sprite."""

    def __init__(self, name: str = "Image") -> None:
        super().__init__(name)
        self.texture_path: str = ""

    widget_type = "UIImage"


class UIScrollView(UIWidget):
    """Container com Rolagem."""

    def __init__(self, name: str = "ScrollView") -> None:
        super().__init__(name)
        self.scroll_y: float = 0.0


class UIInput(UIWidget):
    """Campo de Entrada de Texto."""

    def __init__(self, name: str = "Input") -> None:
        super().__init__(name)
        self.placeholder: str = "Enter text..."


class UIContainer(UIWidget):
    """Container com Auto Layout (Horizontal / Vertical)."""

    def __init__(self, name: str = "Container", layout_mode: str = "Vertical") -> None:
        super().__init__(name)
        self.layout_mode: str = layout_mode


WIDGET_TYPES = {
    cls.__name__: cls
    for cls in (RuntimeUICanvas, UIPanel, UIButton, UILabel, RuntimeUIImage, UIScrollView, UIInput, UIContainer)
}
WIDGET_TYPES.update({"UICanvas": RuntimeUICanvas, "UIImage": RuntimeUIImage})

UICanvas = RuntimeUICanvas
UIImage = RuntimeUIImage


def widget_from_dict(data: dict[str, Any]) -> UIWidget:
    """Rebuild a runtime widget hierarchy from serialized UI data."""
    widget_class = WIDGET_TYPES.get(str(data.get("type", "")), UIWidget)
    widget = widget_class(str(data.get("name", widget_class.__name__)))
    for key in (
        "x", "y", "width", "height", "visible", "bg_color", "text",
        "hover_color", "font_size", "text_color", "texture_path",
        "scroll_y", "placeholder", "layout_mode", "render_mode",
    ):
        if key in data and hasattr(widget, key):
            setattr(widget, key, data[key])
    for child_data in data.get("children", []):
        if isinstance(child_data, dict):
            widget.add_child(widget_from_dict(child_data))
    return widget
