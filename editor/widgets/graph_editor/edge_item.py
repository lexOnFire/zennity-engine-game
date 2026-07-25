"""Generic UI representation of a Graph Edge connection."""
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QPainterPathStroker, QPen, QColor
from PySide6.QtCore import Qt

from .port_item import PORT_COLORS

class GraphEdgeItem(QGraphicsPathItem):
    """Conexão selecionável entre nós."""
    
    def __init__(self, edge_id: str, source_port: str, target_port: str, source_node: str, target_node: str, data_type: str = "any"):
        super().__init__()
        self.edge_id = edge_id
        self.source_port = source_port
        self.target_port = target_port
        self.source_node = source_node
        self.target_node = target_node
        self.data_type = data_type
        
        self.base_color = PORT_COLORS.get(data_type, PORT_COLORS["any"])
        
        self.setPen(QPen(self.base_color, 2.2))
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setData(0, edge_id)
        
    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self._refresh_pen(bool(value))
        return result
        
    def _refresh_pen(self, selected: bool) -> None:
        style = Qt.DashLine if self.data_type == "object" else Qt.SolidLine
        thickness = 3.4 if selected else (2.8 if self.data_type == "object" else 2.2)
        color = QColor("#ffffff") if selected else self.base_color
        self.setPen(QPen(color, thickness, style))
        
    def shape(self) -> QPainterPath:
        # Aumentar a área de clique
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())
