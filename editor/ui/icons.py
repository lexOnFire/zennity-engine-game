"""Glifos monocromáticos usados enquanto o pacote SVG oficial não existe."""

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
