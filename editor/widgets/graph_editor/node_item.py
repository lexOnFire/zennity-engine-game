"""Generic UI representation of a GraphNode."""
from typing import TYPE_CHECKING, Any
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import QRectF, QPointF, Qt
from PySide6.QtGui import QColor, QPen, QBrush

from engine.localization.manager import tr
from .port_item import GraphPortItem

if TYPE_CHECKING:
    from engine.core.metadata.node import NodeDefinition

CATEGORY_COLORS = {
    "logic.category.events": QColor("#d66ba0"),
    "logic.category.movement": QColor("#4c9aff"),
    "logic.category.position": QColor("#3fb6a8"),
    "logic.category.action": QColor("#ae7df0"),
    "logic.category.logic": QColor("#f0a64b"),
    "logic.category.condition": QColor("#50c878"),
    "logic.category.objects": QColor("#47b8c8"),
    "logic.category.variables": QColor("#d5b84b"),
    "logic.category.subgraphs": QColor("#b48ead"),
    "logic.category.math": QColor("#e07a5f"),
    "logic.category.text": QColor("#81b29a"),
}

class GraphNodeItem(QGraphicsRectItem):
    """Nó visual genérico guiado por NodeDefinition."""
    
    WIDTH = 210.0
    MINIMUM_HEIGHT = 80.0

    def __init__(self, node_def: "NodeDefinition", instance_data: dict[str, Any], parent=None):
        self.node_def = node_def
        self.instance_data = instance_data
        
        # Calcular altura baseada nos pinos
        in_count = len(self.node_def.inputs)
        out_count = len(self.node_def.outputs)
        self.height = max(self.MINIMUM_HEIGHT, 48.0 + max(in_count, out_count) * 22.0)
        self.width = self.WIDTH
        
        super().__init__(0.0, 0.0, self.width, self.height, parent)
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        
        pos = instance_data.get("position", [0.0, 0.0])
        self.setPos(float(pos[0]), float(pos[1]))
        self.setZValue(2)
        
        self.setPen(QPen(QColor("#515662"), 1.2))
        self.setBrush(QBrush(QColor("#22242a")))
        
        category_key = getattr(self.node_def, "category_key", "logic.category.logic")
        color = CATEGORY_COLORS.get(category_key, QColor("#7f8b9c"))
        
        self.header = QGraphicsRectItem(0.0, 0.0, self.width, 28.0, self)
        self.header.setPen(Qt.NoPen)
        self.header.setBrush(QBrush(color.darker(155)))
        
        self.title_item = QGraphicsTextItem(tr(self.node_def.name_key), self)
        self.title_item.setDefaultTextColor(QColor("#f2f4f8"))
        self.title_item.setPos(10.0, 3.0)
        font = self.title_item.font()
        font.setBold(True)
        font.setPointSizeF(9.5)
        self.title_item.setFont(font)
        
        self.input_ports: dict[str, GraphPortItem] = {}
        self.output_ports: dict[str, GraphPortItem] = {}
        self.port_labels: list[QGraphicsTextItem] = []
        
        for index, pin in enumerate(self.node_def.inputs):
            y = 43.0 + index * 22.0
            port = GraphPortItem(self, pin, "input", y)
            self.input_ports[pin.id] = port
            
            if not pin.hide_label:
                label = QGraphicsTextItem(tr(pin.label_key), self)
                label.setDefaultTextColor(QColor("#aeb6c5"))
                label.setPos(9.0, y - 12.0)
                self.port_labels.append(label)
                
        for index, pin in enumerate(self.node_def.outputs):
            y = 43.0 + index * 22.0
            port = GraphPortItem(self, pin, "output", y)
            self.output_ports[pin.id] = port
            
            if not pin.hide_label:
                label = QGraphicsTextItem(tr(pin.label_key), self)
                label.setDefaultTextColor(QColor("#aeb6c5"))
                label.setTextWidth(76.0)
                # Alinhamento simples à direita
                label.setPos(self.width - 84.0, y - 12.0) 
                self.port_labels.append(label)
                
    @property
    def node_id(self) -> str:
        return str(self.instance_data.get("id", ""))
        
    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            pos = value if isinstance(value, QPointF) else self.pos()
            self.instance_data["position"] = [round(pos.x(), 2), round(pos.y(), 2)]
            
            if hasattr(self.scene(), "refresh_connections"):
                self.scene().refresh_connections()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self.setPen(QPen(QColor("#f2f4f8") if self.isSelected() else QColor("#515662"), 1.8 if self.isSelected() else 1.2))
        return result

    def record_execution(self) -> None:
        """Registra a execução do nó e ajusta a cor térmica do Heat Map (Azul -> Verde -> Amarelo -> Vermelho)."""
        if not hasattr(self, "execution_count"):
            self.execution_count = 0
        self.execution_count += 1

        # Gradiente térmico baseado no número de execuções
        if self.execution_count > 100:
            heat_color = QColor("#ff4d4d")  # Vermelho (Gargalo / Quente)
        elif self.execution_count > 50:
            heat_color = QColor("#ff9933")  # Laranja
        elif self.execution_count > 20:
            heat_color = QColor("#ffe600")  # Amarelo
        elif self.execution_count > 5:
            heat_color = QColor("#50c878")  # Verde
        else:
            heat_color = QColor("#4c9aff")  # Azul (Frio)

        self.setPen(QPen(heat_color, 2.5))
        self.header.setBrush(QBrush(heat_color.darker(160)))
