from engine.ui.provider import UIProvider
from engine.ui.metadata import WidgetDefinition, UILayoutDefinition
from engine.ui.preview_provider import UIPreviewProvider
from engine.ui.runtime import (
    UIWidget,
    UICanvas,
    UIPanel,
    UIButton,
    UILabel,
    UIImage,
    UIScrollView,
    UIInput,
    UIContainer,
)

# Aliases de compatibilidade retroativa
UIElement = UIWidget
Anchor = str
Pivot = str
Label = UILabel
Button = UIButton
ProgressBar = UIWidget
Panel = UIPanel
UIManager = UIWidget

__all__ = [
    "UIProvider",
    "WidgetDefinition",
    "UILayoutDefinition",
    "UIPreviewProvider",
    "UIWidget",
    "UICanvas",
    "UIPanel",
    "UIButton",
    "UILabel",
    "UIImage",
    "UIScrollView",
    "UIInput",
    "UIContainer",
    "UIElement",
    "Anchor",
    "Pivot",
    "Label",
    "Button",
    "ProgressBar",
    "Panel",
    "UIManager",
]
