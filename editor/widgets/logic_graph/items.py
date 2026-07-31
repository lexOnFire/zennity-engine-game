"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPainterPathStroker,
    QPen, QBrush,
)
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QInputDialog,
    QGraphicsDropShadowEffect,
)

from engine.logic.graph_asset import node_port_definitions
from engine.logic.code_preview import node_code_preview

if TYPE_CHECKING:
    from editor.widgets.logic_graph_editor import LogicGraphEditor

CATEGORY_COLORS = {
    "Eventos": QColor("#d66ba0"),
    "Events": QColor("#ff4fa3"),
    "Movimento": QColor("#4c9aff"),
    "Movement": QColor("#4c8dff"),
    "Posição": QColor("#3fb6a8"),
    "Position": QColor("#20d6c7"),
    "Ação": QColor("#ae7df0"),
    "Action": QColor("#a970ff"),
    "Lógica": QColor("#f0a64b"),
    "Logic": QColor("#ffad42"),
    "Condição": QColor("#50c878"),
    "Condition": QColor("#42e68b"),
    "Objetos": QColor("#47b8c8"),
    "Objects": QColor("#34c8e8"),
    "Components": QColor("#ff9f43"),
    "Variáveis": QColor("#d5b84b"),
    "Variables": QColor("#ffd84a"),
    "Subgrafos": QColor("#b48ead"),
    "Subgraphs": QColor("#d184ff"),
    "Matemática": QColor("#e07a5f"),
    "Math": QColor("#ff725e"),
    "Texto": QColor("#81b29a"),
    "Text": QColor("#6fd6a8"),
    "Personalizado": QColor("#7f8b9c"),
    "Custom": QColor("#8b98ad"),
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

class LogicPortItem(QGraphicsEllipseItem):
    """Porta interativa que inicia e conclui uma conexão por arraste."""

    SIZE = 11.0

    def __init__(self, node: "LogicNodeItem", name: str, direction: str, data_type: str, y: float) -> None:
        x = -self.SIZE / 2 if direction == "input" else node.width - self.SIZE / 2
        super().__init__(x, y - self.SIZE / 2, self.SIZE, self.SIZE, node)
        self.node = node
        self.name = str(name)
        self.direction = str(direction)
        self.data_type = str(data_type)
        self.base_color = PORT_COLORS.get(self.data_type, PORT_COLORS["any"])
        self.setPen(QPen(self.base_color.lighter(135), 2.2))
        self.setBrush(QBrush(QColor("#0b0e14")))
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(5)
        self.setToolTip(f"{self.name} • {self.data_type}")

    def scene_position(self) -> QPointF:
        return self.mapToScene(self.boundingRect().center())

    def set_connection_state(self, state: str = "normal") -> None:
        if state == "candidate":
            self.setBrush(QBrush(QColor("#7ee787")))
            self.setPen(QPen(QColor("#ffffff"), 1.8))
            self.setScale(1.5)
        elif state == "compatible":
            self.setBrush(QBrush(self.base_color.lighter(130)))
            self.setPen(QPen(QColor("#f3f5f9"), 1.2))
            self.setScale(1.16)
        elif state == "invalid":
            self.setBrush(QBrush(QColor("#5b606c")))
            self.setPen(QPen(QColor("#777d89"), 1.0))
            self.setScale(0.9)
        else:
            self.setBrush(QBrush(QColor("#0b0e14")))
            self.setPen(QPen(self.base_color.lighter(135), 2.2))
            self.setScale(1.0)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        if self.data_type == "flow":
            path = QPainterPath()
            path.moveTo(rect.left(), rect.top())
            path.lineTo(rect.left() + rect.width() * 0.55, rect.top())
            path.lineTo(rect.right(), rect.center().y())
            path.lineTo(rect.left() + rect.width() * 0.55, rect.bottom())
            path.lineTo(rect.left(), rect.bottom())
            path.closeSubpath()
            painter.fillPath(path, QBrush(self.base_color if self.brush().color() != QColor("#0b0e14") else QColor("#0e1218")))
            painter.strokePath(path, QPen(self.base_color, 2.0))
        else:
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawEllipse(rect)
            painter.fillPath(QPainterPath(), QBrush())

    def hoverEnterEvent(self, event) -> None:
        if self.node.editor._connection_origin is None:
            self.setScale(1.22)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        if self.node.editor._connection_origin is None:
            self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event) -> None:
        self.node.editor.begin_connection(self)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        self.node.editor.update_connection(event.scenePos())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.node.editor.finish_connection(event.scenePos())
        event.accept()

class LogicEdgeItem(QGraphicsPathItem):
    """Conexão selecionável com cor determinada pelo tipo da porta."""

    def __init__(self, path: QPainterPath, edge_id: str, data_type: str) -> None:
        super().__init__(path)
        self.edge_id = edge_id
        self.data_type = str(data_type)
        self.base_color = PORT_COLORS.get(data_type, PORT_COLORS["any"])
        self._runtime_active = False
        self._validation_level = ""
        self.setPen(QPen(self.base_color, 2.4, Qt.SolidLine, Qt.RoundCap))
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setData(0, edge_id)
        self.setToolTip(
            "Referência de objeto • transporta qual instância será afetada"
            if self.data_type == "object"
            else "Fluxo de execução" if self.data_type == "flow" else f"Valor: {self.data_type}"
        )

    def paint(self, painter: QPainter, option, widget=None) -> None:
        super().paint(painter, option, widget)
        if self._runtime_active and not self.path().isEmpty():
            painter.setRenderHint(QPainter.Antialiasing, True)
            pt = self.path().pointAtPercent(0.5)
            painter.setBrush(QBrush(QColor("#00e5ff")))
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.drawEllipse(pt, 5.0, 5.0)

    def set_runtime_active(self, active: bool) -> None:
        self._runtime_active = bool(active)
        self._refresh_pen(self.isSelected())

    def set_validation_state(self, level: str = "", message: str = "") -> None:
        self._validation_level = str(level)
        self.setToolTip(str(message))
        self._refresh_pen(self.isSelected())

    def _refresh_pen(self, selected: bool) -> None:
        if self._runtime_active:
            self.setPen(QPen(QColor("#55f29a"), 4.2, Qt.SolidLine, Qt.RoundCap))
        elif self._validation_level == "error":
            self.setPen(QPen(QColor("#ff5d62"), 3.4, Qt.DashLine))
        elif self._validation_level == "warning":
            self.setPen(QPen(QColor("#e6b85c"), 3.0, Qt.DashLine))
        else:
            style = Qt.DashLine if self.data_type == "object" else Qt.SolidLine
            self.setPen(QPen(
                QColor("#ffffff") if selected else self.base_color,
                3.6 if selected else (3.0 if self.data_type == "object" else 2.4),
                style,
                Qt.RoundCap,
            ))

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())

from editor.widgets.logic_graph.group_item import LogicGroupItem, LogicGroupResizeHandle

class LogicCommentItem(QGraphicsRectItem):
    """Nota persistente que explica uma região do grafo sem afetar o runtime."""

    def __init__(self, editor: "LogicGraphEditor", data: dict[str, Any]) -> None:
        width = float(data.get("width", 260.0))
        super().__init__(0.0, 0.0, width, 78.0)
        self.editor = editor
        self.data = data
        self.comment_id = str(data["id"])
        self.setPos(*data.get("position", [0.0, 0.0]))
        self.setZValue(1)
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        color = QColor(str(data.get("color", "#6b5b2f")))
        color.setAlpha(190)
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#d9b85f"), 1.4))
        self.text_item = QGraphicsTextItem(str(data.get("text", "Comentário")), self)
        self.text_item.setDefaultTextColor(QColor("#fff3c4"))
        self.text_item.setTextWidth(width - 16.0)
        self.text_item.setPos(8.0, 7.0)
        self.setToolTip("Duplo clique edita o comentário")

    def mouseDoubleClickEvent(self, event) -> None:
        text_value, accepted = QInputDialog.getMultiLineText(
            None, "Editar comentário", "Texto", str(self.data.get("text", "Comentário"))
        )
        if accepted:
            self.data["text"] = text_value
            self.text_item.setPlainText(text_value)
            self.editor.mark_dirty()
        event.accept()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            position = value if isinstance(value, QPointF) else self.pos()
            self.data["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.mark_dirty()
        return result

class LogicFlipControl(QGraphicsTextItem):
    """Controle pequeno que alterna frente e pseudocódigo do bloco."""

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__("</>", node)
        self.node = node
        self.setDefaultTextColor(QColor("#dce6f2"))
        font = self.font()
        font.setBold(True)
        font.setPointSizeF(8.0)
        self.setFont(font)
        self.setPos(node.width - 52.0, 2.0)
        self.setToolTip("Show editable code preview")
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event) -> None:
        self.node.toggle_code_preview()
        event.accept()

class LogicCollapseControl(QGraphicsTextItem):
    """Recolhe o corpo do bloco sem perder suas conexões."""

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__("−", node)
        self.node = node
        self.setDefaultTextColor(QColor("#dce6f2"))
        font = self.font()
        font.setBold(True)
        font.setPointSizeF(10.0)
        self.setFont(font)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Recolher bloco")

    def refresh(self) -> None:
        self.setPlainText("+" if self.node.collapsed else "−")
        self.setToolTip("Expandir bloco" if self.node.collapsed else "Recolher bloco")
        self.setPos(self.node.width - 76.0, 1.0)

    def mousePressEvent(self, event) -> None:
        self.node.toggle_collapsed()
        event.accept()

class LogicResizeHandle(QGraphicsRectItem):
    """Alça inferior direita para redimensionar um bloco expandido."""

    SIZE = 14.0

    def __init__(self, node: "LogicNodeItem") -> None:
        super().__init__(0.0, 0.0, self.SIZE, self.SIZE, node)
        self.node = node
        self._origin = QPointF()
        self._initial_size = (node.width, node.height)
        self.setPen(QPen(QColor("#7f8796"), 1.0))
        self.setBrush(QBrush(QColor("#353943")))
        self.setCursor(Qt.SizeFDiagCursor)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setZValue(8)
        self.setToolTip("Arraste para redimensionar")

    def mousePressEvent(self, event) -> None:
        self._origin = event.scenePos()
        self._initial_size = (self.node.width, self.node.expanded_height)
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        delta = event.scenePos() - self._origin
        self.node.resize_to(self._initial_size[0] + delta.x(), self._initial_size[1] + delta.y())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.node.editor.mark_dirty()
        event.accept()

from editor.widgets.logic_graph.item_runtime_mixin import LogicNodeItemRuntimeMixin
from editor.widgets.logic_graph.item_geometry_mixin import LogicNodeItemGeometryMixin


class LogicNodeItem(LogicNodeItemGeometryMixin, LogicNodeItemRuntimeMixin, QGraphicsRectItem):
    WIDTH = 242.0
    MINIMUM_WIDTH = 220.0
    MAXIMUM_WIDTH = 520.0
    MINIMUM_HEIGHT = 132.0
    MAXIMUM_HEIGHT = 720.0
    COLLAPSED_HEIGHT = 42.0
    HEADER_HEIGHT = 42.0
    PORT_START_Y = 60.0
    PORT_SPACING = 28.0

    def __init__(self, editor: "LogicGraphEditor", node: dict[str, Any]) -> None:
        ports = node_port_definitions(node)
        self.input_definitions = ports["inputs"]
        self.output_definitions = ports["outputs"]
        port_rows = max(len(self.input_definitions), len(self.output_definitions), 1)
        self.natural_height = max(
            self.MINIMUM_HEIGHT + 18.0,
            100.0 + port_rows * self.PORT_SPACING,
        )
        editor_state = node.setdefault("editor", {})
        self.width = max(self.MINIMUM_WIDTH, min(self.MAXIMUM_WIDTH, float(editor_state.get("width", self.WIDTH))))
        stored_height = float(editor_state.get("height", 0.0))
        self.expanded_height = max(self.natural_height, min(self.MAXIMUM_HEIGHT, stored_height or self.natural_height))
        self.collapsed = bool(editor_state.get("collapsed", False))
        self.height = self.COLLAPSED_HEIGHT if self.collapsed else self.expanded_height
        editor_state.update({"collapsed": self.collapsed, "width": self.width, "height": self.expanded_height})
        super().__init__(0.0, 0.0, self.width, self.height)
        self.editor = editor
        self.node = node
        self._show_code = False
        self._hovered = False
        self._fanout_count = 0
        self._target_hint = ""
        self._target_is_implicit = False
        self._runtime_display: tuple[bool, dict[str, Any] | None, str, bool] = (False, None, "", False)
        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
            | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setPos(float(node["position"][0]), float(node["position"][1]))
        self.setZValue(2)
        self.setPen(QPen(QColor("#30394a"), 1.2))
        self.setBrush(QBrush(QColor("#151922")))
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18.0)
        shadow.setOffset(0.0, 5.0)
        color = CATEGORY_COLORS.get(str(node.get("category")), CATEGORY_COLORS["Personalizado"])
        self.category_color = color
        shadow_color = QColor(color)
        shadow_color.setAlpha(75)
        shadow.setColor(shadow_color)
        self.setGraphicsEffect(shadow)
        self.header = QGraphicsRectItem(0.0, 0.0, self.width, 28.0, self)
        self.header.setPen(Qt.NoPen)
        self.header.setBrush(Qt.NoBrush)
        self.header.hide()
        self.accent = QGraphicsRectItem(0.0, 0.0, 4.0, self.height, self)
        self.accent.setPen(Qt.NoPen)
        self.accent.setBrush(QBrush(color))
        self.breakpoint_item = QGraphicsEllipseItem(self.width - 20.0, 8.0, 10.0, 10.0, self)
        self.breakpoint_item.setPen(QPen(QColor("#ffd7d9"), 1.0))
        self.breakpoint_item.setBrush(QBrush(QColor("#ff4d55")))
        self.breakpoint_item.setToolTip("Breakpoint")
        self.breakpoint_item.setVisible(False)

        self.title_item = QGraphicsTextItem(str(node.get("title", "Nó")), self)
        self.title_item.setDefaultTextColor(QColor("#f5f7fb"))
        self.title_item.setPos(13.0, 3.0)
        font = self.title_item.font()
        font.setBold(True)
        font.setFamily("Segoe UI")
        font.setPointSizeF(10.0)
        self.title_item.setFont(font)
        self.category_item = QGraphicsTextItem(
            str(node.get("category", "Custom")).upper(), self
        )
        self.category_item.setDefaultTextColor(color.lighter(170))
        self.category_item.setPos(13.0, 21.0)
        category_font = self.category_item.font()
        category_font.setFamily("Segoe UI")
        category_font.setBold(True)
        category_font.setPointSizeF(6.8)
        category_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.1)
        self.category_item.setFont(category_font)
        self.flip_control = LogicFlipControl(self)
        self.collapse_control = LogicCollapseControl(self)

        self.summary_item = QGraphicsTextItem("", self)
        self.summary_item.setDefaultTextColor(QColor("#7f8a9d"))
        self.summary_item.setTextWidth(self.width - 22.0)
        self.summary_item.setPos(10.0, self.height - 25.0)
        summary_font = self.summary_item.font()
        summary_font.setPointSizeF(8.5)
        self.summary_item.setFont(summary_font)
        self.target_item = QGraphicsTextItem("", self)
        self.target_item.setDefaultTextColor(QColor("#75d5df"))
        self.target_item.setTextWidth(self.width - 22.0)
        self.target_item.setPos(10.0, self.height - 45.0)
        target_font = self.target_item.font()
        target_font.setBold(True)
        target_font.setPointSizeF(8.3)
        self.target_item.setFont(target_font)
        self.target_item.hide()
        self.debug_item = QGraphicsTextItem("", self)
        self.debug_item.setDefaultTextColor(QColor("#7ee787"))
        self.debug_item.setTextWidth(self.width - 22.0)
        self.debug_item.setPos(10.0, self.height - 25.0)
        self.debug_item.setVisible(False)
        self.code_item = QGraphicsTextItem("", self)
        self.code_item.setDefaultTextColor(QColor("#b9e3c6"))
        self.code_item.setTextWidth(self.width - 18.0)
        self.code_item.setPos(8.0, 32.0)
        code_font = self.code_item.font()
        code_font.setFamily("Consolas")
        code_font.setPointSizeF(7.8)
        self.code_item.setFont(code_font)
        self.code_item.setToolTip("Double-click this node to edit the code values.")
        self.code_item.setVisible(False)

        self.input_ports: dict[str, LogicPortItem] = {}
        self.output_ports: dict[str, LogicPortItem] = {}
        self.port_labels: list[QGraphicsTextItem] = []
        for index, (name, data_type) in enumerate(self.input_definitions):
            y = self.PORT_START_Y + index * self.PORT_SPACING
            port = LogicPortItem(self, name, "input", data_type, y)
            self.input_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setPos(13.0, y - 12.0)
            label_font = label.font()
            label_font.setFamily("Segoe UI")
            label_font.setPointSizeF(8.0)
            label.setFont(label_font)
            self.port_labels.append(label)
        for index, (name, data_type) in enumerate(self.output_definitions):
            y = self.PORT_START_Y + index * self.PORT_SPACING
            port = LogicPortItem(self, name, "output", data_type, y)
            self.output_ports[name] = port
            label = QGraphicsTextItem(name, self)
            label.setDefaultTextColor(QColor("#aeb6c5"))
            label.setTextWidth(76.0)
            label.setPos(self.width - 84.0, y - 12.0)
            label_font = label.font()
            label_font.setFamily("Segoe UI")
            label_font.setPointSizeF(8.0)
            label.setFont(label_font)
            self.port_labels.append(label)
        self.resize_handle = LogicResizeHandle(self)
        self.refresh_text()
        self._apply_geometry(notify=False)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        outer = QPainterPath()
        outer.addRoundedRect(self.rect(), 9.0, 9.0)
        body_gradient = QLinearGradient(0.0, 0.0, 0.0, self.height)
        body_gradient.setColorAt(0.0, self.category_color.darker(340))
        body_gradient.setColorAt(0.42, QColor("#141a26"))
        body_gradient.setColorAt(1.0, QColor("#0d1119"))
        painter.fillPath(outer, QBrush(body_gradient))

        header_rect = QRectF(
            1.0, 1.0, self.width - 2.0,
            min(self.HEADER_HEIGHT, self.height - 2.0),
        )
        header = QPainterPath()
        header.addRoundedRect(header_rect, 8.0, 8.0)
        gradient = QLinearGradient(0.0, 0.0, self.width, 0.0)
        gradient.setColorAt(0.0, self.category_color.darker(112))
        gradient.setColorAt(0.62, self.category_color.darker(155))
        gradient.setColorAt(1.0, self.category_color.darker(230))
        painter.fillPath(header, QBrush(gradient))
        if self.height > self.HEADER_HEIGHT:
            painter.fillRect(
                QRectF(1.0, self.HEADER_HEIGHT - 8.0, self.width - 2.0, 9.0),
                QBrush(gradient),
            )

        painter.fillRect(
            QRectF(0.0, 0.0, self.width, 3.0),
            QBrush(self.category_color.lighter(125)),
        )

        if not self.collapsed:
            rows = max(len(self.input_definitions), len(self.output_definitions), 1)
            for index in range(rows):
                row_y = self.PORT_START_Y - 15.0 + index * self.PORT_SPACING
                if index % 2 == 0:
                    painter.fillRect(
                        QRectF(7.0, row_y, self.width - 14.0, self.PORT_SPACING),
                        QColor(
                            self.category_color.red(),
                            self.category_color.green(),
                            self.category_color.blue(),
                            18,
                        ),
                    )
            footer_y = self.height - 34.0
            painter.setPen(QPen(QColor("#252d3b"), 1.0))
            painter.drawLine(
                QPointF(10.0, footer_y),
                QPointF(self.width - 10.0, footer_y),
            )

        if self.isSelected():
            painter.setPen(QPen(QColor(124, 92, 255, 55), 7.0))
            painter.drawPath(outer)
        elif self._hovered:
            hover = QColor(self.category_color)
            hover.setAlpha(90)
            painter.setPen(QPen(hover, 4.0))
            painter.drawPath(outer)
        painter.setPen(self.pen())
        painter.drawPath(outer)

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    @property
    def node_id(self) -> str:
        return str(self.node["id"])

    def input_position(self, port_name: str = "in") -> QPointF:
        if self.collapsed:
            return self.mapToScene(QPointF(0.0, self.COLLAPSED_HEIGHT / 2.0))
        port = self.input_ports.get(port_name) or next(iter(self.input_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(
            QPointF(0.0, self.PORT_START_Y)
        )

    def output_position(self, port_name: str = "next") -> QPointF:
        if self.collapsed:
            return self.mapToScene(QPointF(self.width, self.COLLAPSED_HEIGHT / 2.0))
        port = self.output_ports.get(port_name) or next(iter(self.output_ports.values()), None)
        return port.scene_position() if port is not None else self.mapToScene(
            QPointF(self.width, self.PORT_START_Y)
        )

    def resize_to(self, width: float, height: float) -> None:
        self.width = max(self.MINIMUM_WIDTH, min(self.MAXIMUM_WIDTH, float(width)))
        self.expanded_height = max(self.natural_height, min(self.MAXIMUM_HEIGHT, float(height)))
        self.node.setdefault("editor", {}).update({
            "collapsed": self.collapsed,
            "width": round(self.width, 2),
            "height": round(self.expanded_height, 2),
        })
        self._apply_geometry()



    def refresh_text(self) -> None:
        properties = self.node.get("properties", {})
        if str(self.node.get("type", "")).startswith("event_") and self._fanout_count:
            summary = f"{self._fanout_count} ação(ões) conectada(s) • arraste para adicionar"
        elif str(self.node.get("type", "")) == "create_prefab":
            count = len(properties.get("exposed_properties", [])) if isinstance(properties.get("exposed_properties"), list) else 0
            summary = f"{Path(str(properties.get('path', 'Prefab'))).stem or 'Prefab'} • {count} propriedade(s) exposta(s)"
        elif properties:
            summary = "  •  ".join(f"{key}: {value}" for key, value in list(properties.items())[:2])
        else:
            summary = str(self.node.get("category", ""))
        self.summary_item.setPlainText(summary)
        self.code_item.setPlainText(node_code_preview(self.node))

    def set_fanout_count(self, count: int) -> None:
        self._fanout_count = max(0, int(count))
        self.refresh_text()

    def set_target_hint(self, text: str = "", implicit: bool = False) -> None:
        self._target_hint = str(text)
        self._target_is_implicit = bool(implicit)
        self.target_item.setPlainText(self._target_hint)
        self.target_item.setDefaultTextColor(QColor("#e6b85c") if implicit else QColor("#75d5df"))
        self.target_item.setToolTip(
            "Este alvo veio automaticamente do fluxo de criação anterior. Conecte a porta target para substituí-lo."
            if implicit else "Objeto que este bloco afetará"
        )
        self.target_item.setVisible(bool(text) and not self.collapsed and not self._show_code)
        self.setToolTip(self.target_item.toolTip() if text else "")

    def mouseDoubleClickEvent(self, event) -> None:
        if self._show_code and self.editor.edit_node_code_value(self):
            event.accept()
            return
        self.editor.toggle_breakpoint(self.node_id)
        event.accept()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            from PySide6.QtCore import QPointF
            position = value if isinstance(value, QPointF) else self.pos()
            self.node["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.refresh_connections()
            self.editor.mark_dirty()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self._update_border_style()
        return result

