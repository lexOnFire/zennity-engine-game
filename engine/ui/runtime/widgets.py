"""Hierarquia Runtime de Widgets de UI (UICanvas, UIPanel, UIButton, UILabel, UIImage, UIScrollView, UIInput, UIContainer)."""
from __future__ import annotations
from typing import List, Optional


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
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "children": [c.serialize() for c in self.children],
        }


class UICanvas(UIWidget):
    """Container Raiz de Interface para renderização."""

    def __init__(self, name: str = "Canvas") -> None:
        super().__init__(name)
        self.width = 1920.0
        self.height = 1080.0


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


class UIImage(UIWidget):
    """Exibição de Imagem ou Sprite."""

    def __init__(self, name: str = "Image") -> None:
        super().__init__(name)
        self.texture_path: str = ""


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
