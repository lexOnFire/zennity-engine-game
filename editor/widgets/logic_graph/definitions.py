"""Shared visual definitions for the Logic Graph editor.

Keeping these values outside the editor facade prevents the mixins from importing
the concrete QWidget and forming a circular dependency.
"""

from PySide6.QtGui import QColor
from engine.i18n import tr

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
    "Events": QColor("#d66ba0"),
    "Movement": QColor("#4c9aff"),
    "Position": QColor("#3fb6a8"),
    "Action": QColor("#ae7df0"),
    "Logic": QColor("#f0a64b"),
    "Condition": QColor("#50c878"),
    "Objects": QColor("#47b8c8"),
    "Variables": QColor("#d5b84b"),
    "Subgraphs": QColor("#b48ead"),
    "Math": QColor("#e07a5f"),
    "Text": QColor("#81b29a"),
    "Custom": QColor("#7f8b9c"),
}

PORT_COLORS = {
    "flow": QColor("#d9dde7"),
    "number": QColor("#58a6ff"),
    "bool": QColor("#50c878"),
    "text": QColor("#e6b85c"),
    "object": QColor("#47b8c8"),
    "movement": QColor("#ff8c69"),
    "any": QColor("#ae7df0"),
}

NODE_DESCRIPTIONS = I18nNodeDesc()

PROPERTY_LABELS = I18nProp()

NODE_PROPERTY_LABELS = I18nNodeProp()
