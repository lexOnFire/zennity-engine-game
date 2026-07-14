"""Catálogo de ícones do editor e fallback textual de compatibilidade."""

from pathlib import Path


ICON_DIRECTORY = Path(__file__).with_name("svg")

TOOLBAR_ICONS = {
    "Novo": "new",
    "Abrir": "open",
    "Salvar": "save",
    "Desfazer": "undo",
    "Refazer": "redo",
    "Select": "select",
    "Move": "move",
    "Rotate": "rotate",
    "Scale": "scale",
    "Snap: OFF": "snap",
    "Play": "play",
    "Pause": "pause",
    "Stop": "stop",
}

TOOLBAR_GLYPHS = {
    "Novo": "＋",
    "Abrir": "⌂",
    "Salvar": "▣",
    "Desfazer": "↶",
    "Refazer": "↷",
    "Select": "◇",
    "Move": "✥",
    "Rotate": "↻",
    "Scale": "↗",
    "Snap: OFF": "#",
    "Play": "▶",
    "Pause": "Ⅱ",
    "Stop": "■",
}

COMPONENT_GLYPHS = {
    "transform": "◆",
    "sprite": "▧",
    "audio": "♪",
    "rigidbody": "●",
    "collider": "□",
    "camera": "▣",
    "ui": "▤",
    "script": "<>",
}


def component_title(kind: str, title: str) -> str:
    return f"{COMPONENT_GLYPHS.get(kind, '•')}  {title}"


def icon_path(name: str) -> Path:
    """Retorna um SVG conhecido sem importar Qt em testes e ferramentas CLI."""
    path = ICON_DIRECTORY / f"{name}.svg"
    if not path.is_file():
        raise KeyError(f"Ícone desconhecido: {name}")
    return path


def editor_icon(name: str):
    """Cria QIcon sob demanda; mantém este módulo utilizável sem PySide6."""
    from PySide6.QtGui import QIcon

    return QIcon(str(icon_path(name)))
