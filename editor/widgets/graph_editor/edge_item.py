"""Generic UI representation of a Graph Edge connection.

Features:
  - Bezier cubic curve with color matched to pin data-type
  - Animated 'marching ants' dash when selected
  - Wide invisible hit-area for easy click-to-select
  - Hover highlight
  - type-mismatch visual warning (orange dashed)
"""
from __future__ import annotations
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem
from PySide6.QtGui import QPainterPath, QPainterPathStroker, QPen, QColor
from PySide6.QtCore import Qt, QPointF

from .port_item import PORT_COLORS


class GraphEdgeItem(QGraphicsPathItem):
    """Conexão selecionável entre dois pinos de nós distintos."""

    # Data-type pairs that are considered compatible
    COMPATIBLE_PAIRS: frozenset[frozenset[str]] = frozenset({
        frozenset({"number", "float"}),
        frozenset({"number", "int"}),
        frozenset({"float", "int"}),
        frozenset({"any", "exec"}),
        frozenset({"any", "object"}),
    })

    def __init__(
        self,
        edge_id: str,
        source_port: str,
        target_port: str,
        source_node: str,
        target_node: str,
        data_type: str = "any",
        target_data_type: str | None = None,
    ):
        super().__init__()
        self.edge_id = edge_id
        self.source_port = source_port
        self.target_port = target_port
        self.source_node = source_node
        self.target_node = target_node
        self.data_type = data_type
        self.target_data_type = target_data_type or data_type

        # Type compatibility check
        self._type_mismatch = self._check_mismatch()

        self.base_color = PORT_COLORS.get(data_type, PORT_COLORS["any"])
        self._hovered = False

        self._refresh_pen(selected=False)
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setData(0, edge_id)

    # ── Type Checking ──────────────────────────────────────────────────────────
    def _check_mismatch(self) -> bool:
        if self.data_type == self.target_data_type:
            return False
        if "any" in (self.data_type, self.target_data_type):
            return False
        if "exec" in (self.data_type, self.target_data_type):
            return self.data_type != self.target_data_type
        pair = frozenset({self.data_type, self.target_data_type})
        return pair not in self.COMPATIBLE_PAIRS

    # ── Visual ────────────────────────────────────────────────────────────────
    def _refresh_pen(self, selected: bool) -> None:
        if self._type_mismatch:
            color = QColor("#e07a3f")
            style = Qt.DashLine
            width = 2.2
        elif selected:
            color = QColor("#ffffff")
            style = Qt.SolidLine
            width = 3.2
        elif self._hovered:
            color = self.base_color.lighter(140)
            style = Qt.SolidLine
            width = 2.8
        else:
            color = self.base_color
            style = Qt.DashLine if self.data_type == "object" else Qt.SolidLine
            width = 2.0

        self.setPen(QPen(color, width, style))

    # ── Path ──────────────────────────────────────────────────────────────────
    def update_path(self, p1: QPointF, p2: QPointF) -> None:
        """Recalculate the bezier path given two scene positions."""
        dx = abs(p2.x() - p1.x()) * 0.5 + 40.0
        path = QPainterPath(p1)
        path.cubicTo(
            QPointF(p1.x() + dx, p1.y()),
            QPointF(p2.x() - dx, p2.y()),
            p2,
        )
        self.setPath(path)

    # ── Qt Overrides ──────────────────────────────────────────────────────────
    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self._refresh_pen(bool(value))
        return result

    def hoverEnterEvent(self, event) -> None:
        self._hovered = True
        self._refresh_pen(self.isSelected())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self._hovered = False
        self._refresh_pen(self.isSelected())
        super().hoverLeaveEvent(event)

    def shape(self) -> QPainterPath:
        """Aumenta a área de clique para 14 px ao redor da curva."""
        stroker = QPainterPathStroker()
        stroker.setWidth(14.0)
        return stroker.createStroke(self.path())
