"""Generic UI representation of a GraphNode."""
from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import QRectF

class NodeItem(QGraphicsItem):
    def __init__(self, node_data, parent=None):
        super().__init__(parent)
        self.node_data = node_data
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        
    def boundingRect(self):
        return QRectF(0, 0, 150, 100)
        
    def paint(self, painter, option, widget):
        painter.drawRect(self.boundingRect())
        painter.drawText(self.boundingRect(), self.node_data.metadata.name)
