"""
engine/ui/__init__.py
─────────────────────────────────────────────────────────────
Ponto de entrada público do sistema de UI de runtime da Zennity Engine.

BUG FIX (ago/2026): este arquivo reexportava o sistema de widgets do
*editor* (engine.ui.runtime — usado pelo UI Builder do PySide6) e depois
sobrescrevia os nomes reais do sistema de UI de *runtime* com aliases
incorretos:

    Anchor      = str          # era um Enum de verdade em engine.ui.base
    Pivot       = str          # idem
    ProgressBar = UIWidget     # era engine.ui.progress_bar.ProgressBar
    UIManager   = UIWidget     # era o singleton em engine.ui.ui_manager
    Label       = UILabel      # classe errada (widget do editor)
    Button      = UIButton     # idem
    Panel       = UIPanel      # idem

Qualquer código que fizesse `from engine.ui import UIManager, Anchor,
Pivot, ProgressBar, Label, Button, Panel, UICanvas` (como os demos oficiais
demo_ui.py e demo_scene_manager.py) recebia as classes erradas e quebrava
em runtime (ex.: `UIManager.instance()` → AttributeError, pois UIWidget
não tem esse método).

Nada no projeto depende da reexportação do sistema de widgets do editor
através de `engine.ui` — o único consumidor (editor/ui_builder/
ui_builder_dock.py) já importa diretamente de `engine.ui.runtime`. Por
isso este módulo agora expõe apenas as classes reais do runtime.
"""

from engine.ui.provider import UIProvider
from engine.ui.metadata import WidgetDefinition, UILayoutDefinition
from engine.ui.preview_provider import UIPreviewProvider
from engine.ui.data_binding import UIDataBindingManager, UIBinding
from engine.ui.runtime_components import Canvas, LabelComponent, ButtonComponent
from engine.ui.ui_binder import UIBinder
from engine.ui.dialogue_manager import DialogueManager

# ── Sistema de UI de runtime (o que Scene/GameScene realmente usam) ────────
from engine.ui.base import Anchor, Pivot, UIElement
from engine.ui.canvas import UICanvas
from engine.ui.panel import Panel
from engine.ui.label import Label
from engine.ui.button import Button
from engine.ui.progress_bar import ProgressBar
from engine.ui.image import UIImage
from engine.ui.ui_manager import UIManager

__all__ = [
    "UIProvider",
    "WidgetDefinition",
    "UILayoutDefinition",
    "UIPreviewProvider",
    "UIDataBindingManager",
    "UIBinding",
    "Canvas",
    "LabelComponent",
    "ButtonComponent",
    "UIBinder",
    "DialogueManager",
    "Anchor",
    "Pivot",
    "UIElement",
    "UICanvas",
    "Panel",
    "Label",
    "Button",
    "ProgressBar",
    "UIImage",
    "UIManager",
]
