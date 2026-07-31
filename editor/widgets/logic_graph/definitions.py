"""Shared visual definitions for the Logic Graph editor.

Keeping these values outside the editor facade prevents the mixins from importing
the concrete QWidget and forming a circular dependency.
"""

from PySide6.QtGui import QColor
from engine.localization import tr

class I18nNodeDesc:
    def get(self, key, default=None):
        return tr(f'graph.nodes.{key}.description', default)

class I18nProp:
    def get(self, key, default=None):
        return tr(f'graph.properties.{key}', default)

class I18nNodeProp:
    def get(self, key, default=None):
        class Inner:
            def get(self, prop, d2=None):
                return tr(f'graph.node_properties.{key}.{prop}', d2)
        return Inner()



CATEGORY_COLORS = {
    "Events": QColor("#e74c3c"),
    "Eventos": QColor("#e74c3c"),
    "Input": QColor("#00e5ff"),
    "Movement": QColor("#29b6f6"),
    "Movimento": QColor("#29b6f6"),
    "Position": QColor("#26a69a"),
    "Posição": QColor("#26a69a"),
    "Action": QColor("#ff7043"),
    "Ação": QColor("#ff7043"),
    "Logic": QColor("#ab47bc"),
    "Lógica": QColor("#ab47bc"),
    "Condition": QColor("#ab47bc"),
    "Condição": QColor("#ab47bc"),
    "Math": QColor("#66bb6a"),
    "Matemática": QColor("#66bb6a"),
    "Objects": QColor("#78909c"),
    "Objetos": QColor("#78909c"),
    "Components": QColor("#ffa000"),
    "Spawning": QColor("#ff7043"),
    "Animation": QColor("#ec407a"),
    "Audio": QColor("#26c6da"),
    "UI": QColor("#ffca28"),
    "Variables": QColor("#ffa000"),
    "Variáveis": QColor("#ffa000"),
    "Subgraphs": QColor("#8d6e63"),
    "Subgrafos": QColor("#8d6e63"),
    "Custom": QColor("#78909c"),
    "Personalizado": QColor("#78909c"),
}

PORT_COLORS = {
    "flow": QColor("#ffffff"),
    "number": QColor("#00e5ff"),
    "bool": QColor("#e74c3c"),
    "text": QColor("#ffca28"),
    "object": QColor("#ab47bc"),
    "movement": QColor("#29b6f6"),
    "any": QColor("#b0bec5"),
}

NODE_DESCRIPTIONS = I18nNodeDesc()

PROPERTY_LABELS = I18nProp()

NODE_PROPERTY_LABELS = I18nNodeProp()
