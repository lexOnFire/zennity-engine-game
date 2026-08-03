"""Generic Port Item for Graph Canvas."""
from typing import TYPE_CHECKING
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtWidgets import QGraphicsEllipseItem

from engine.localization.manager import tr

if TYPE_CHECKING:
    from .node_item import GraphNodeItem
    from engine.core.metadata.pin import PinDefinition

PORT_COLORS = {
    "exec": QColor("#d9dde7"),
    "number": QColor("#58a6ff"),
    "int": QColor("#58a6ff"),
    "float": QColor("#58a6ff"),
    "bool": QColor("#50c878"),
    "string": QColor("#e6b85c"),
    "object": QColor("#47b8c8"),
    "movement": QColor("#ff8c69"),
    "any": QColor("#ae7df0"),
    "vector2": QColor("#e07a5f"),
    "vector3": QColor("#e07a5f"),
    "color": QColor("#d66ba0")
}

class GraphPortItem(QGraphicsEllipseItem):
    """Porta interativa que inicia e conclui conexões."""
    SIZE = 12.0

    def __init__(self, node: "GraphNodeItem", pin_def: "PinDefinition", direction: str, y: float):
        x = -self.SIZE / 2 if direction == "input" else node.width - self.SIZE / 2
        super().__init__(x, y - self.SIZE / 2, self.SIZE, self.SIZE, node)
        
        self.node = node
        self.pin_def = pin_def
        self.direction = direction  # "input" or "output"
        self.name = pin_def.id
        self.data_type = str(pin_def.pin_type)
        
        self.base_color = PORT_COLORS.get(self.data_type, PORT_COLORS["any"])
        self.setPen(QPen(QColor("#f3f5f9"), 1.0))
        self.setBrush(QBrush(self.base_color))
        self.setTransformOriginPoint(self.boundingRect().center())
        
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(5)
        
        label_text = tr(pin_def.label_key)
        self.setToolTip(f"{label_text} • {self.data_type}")

    def scene_position(self) -> QPointF:
        return self.mapToScene(self.boundingRect().center())

    def hoverEnterEvent(self, event) -> None:
        self.setScale(1.22)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    # Todo: Edge creation interaction
    def mousePressEvent(self, event) -> None:
        if hasattr(self.node.scene(), "begin_connection"):
            self.node.scene().begin_connection(self)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        if hasattr(self.node.scene(), "update_connection"):
            self.node.scene().update_connection(event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        if hasattr(self.node.scene(), "finish_connection"):
            self.node.scene().finish_connection(event.scenePos())
        event.accept()
