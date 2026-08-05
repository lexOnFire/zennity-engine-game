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

def format_readable_title(raw: str, node_id: str) -> str:
    if raw and not raw.startswith("node.") and not raw.startswith("bt."):
        return raw
    titles = {
        "bt.sequence": "Sequência (Sequence)",
        "bt.selector": "Seletor (Selector)",
        "bt.inverter": "Inversor (Inverter)",
        "bt.wait": "Esperar (Wait)",
        "bt.move_to": "Mover Até (MoveTo)",
        "bt.repeat": "Repetir (Repeat)",
        "bt.cooldown": "Cooldown (Recarga)",
        "bt.target_in_range": "Alvo no Alcance",
        "bt.parameter_condition": "Condição de Parâmetro",
        "bt.chase": "Perseguir Alvo",
        "bt.patrol": "Patrulhar",
        "bt.attack": "Atacar Alvo",
        "bt.play_animation": "Reproduzir Animação",
    }
    return titles.get(node_id, titles.get(raw, node_id.replace("bt.", "").replace("_", " ").title()))


def format_readable_pin_label(raw: str, pin_id: str) -> str:
    if raw and not raw.startswith("pin.") and not raw.endswith(".label"):
        return raw
    labels = {
        "in": "In",
        "out": "Out",
        "out_1": "Saída 1",
        "out_2": "Saída 2",
        "child": "Filho",
        "duration": "Duração (s)",
        "target_pos": "Posição Alvo",
        "speed": "Velocidade",
        "target": "Alvo",
        "count": "Contagem",
        "seconds": "Segundos",
        "distance": "Distância",
        "parameter": "Parâmetro",
        "operator": "Operador",
        "value": "Valor",
        "stop_distance": "Dist. Parada",
        "point_a": "Ponto A",
        "point_b": "Ponto B",
        "damage": "Dano",
        "range": "Alcance",
        "animation": "Animação",
    }
    return labels.get(pin_id, pin_id.replace("_", " ").title())


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
        
        raw_name = tr(self.node_def.name_key, fallback=self.node_def.name_key)
        title_text = format_readable_title(raw_name, self.node_def.id)
        self.title_item = QGraphicsTextItem(title_text, self)
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
                raw_pin_label = tr(pin.label_key, fallback=getattr(pin, "label", pin.id))
                pin_text = format_readable_pin_label(raw_pin_label, pin.id)
                label = QGraphicsTextItem(pin_text, self)
                label.setDefaultTextColor(QColor("#aeb6c5"))
                label.setPos(9.0, y - 12.0)
                self.port_labels.append(label)
                
        for index, pin in enumerate(self.node_def.outputs):
            y = 43.0 + index * 22.0
            port = GraphPortItem(self, pin, "output", y)
            self.output_ports[pin.id] = port
            
            if not pin.hide_label:
                raw_pin_label = tr(pin.label_key, fallback=getattr(pin, "label", pin.id))
                pin_text = format_readable_pin_label(raw_pin_label, pin.id)
                label = QGraphicsTextItem(pin_text, self)
                label.setDefaultTextColor(QColor("#aeb6c5"))
                text_w = label.boundingRect().width()
                label.setPos(self.width - text_w - 14.0, y - 12.0) 
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

    def set_active_execution(self, active: bool = True) -> None:
        """Destaca o nó quando em execução (em tempo real durante Play Mode)."""
        if active:
            self.setPen(QPen(QColor("#ffff00"), 4.0))  # 🟡 Amarelo brilhante
            self.header.setBrush(QBrush(QColor("#ffaa00")))
            self.setZValue(100)  # Trazer para frente
        else:
            self.setZValue(2)  # Voltar ao normal
            self.setPen(QPen(QColor("#515662"), 1.2))
            category_key = getattr(self.node_def, "category_key", "logic.category.logic")
            color = CATEGORY_COLORS.get(category_key, QColor("#7f8b9c"))
            self.header.setBrush(QBrush(color.darker(155)))
