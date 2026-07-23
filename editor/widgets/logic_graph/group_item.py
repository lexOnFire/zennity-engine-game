"""Item de grupo visual para organização de blocos no Logic Graph."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QInputDialog,
)

if TYPE_CHECKING:
    from editor.widgets.logic_graph_editor import LogicGraphEditor


class LogicGroupResizeHandle(QGraphicsRectItem):
    SIZE = 14.0

    def __init__(self, group: "LogicGroupItem") -> None:
        super().__init__(0.0, 0.0, self.SIZE, self.SIZE, group)
        self.group = group
        self._origin = QPointF()
        self._initial_size = (group.rect().width(), group.rect().height())
        self.setBrush(QBrush(QColor("#55789b")))
        self.setPen(Qt.NoPen)
        self.setCursor(Qt.SizeFDiagCursor)
        self.setZValue(3)

    def mousePressEvent(self, event) -> None:
        self._origin = event.scenePos()
        self._initial_size = (self.group.rect().width(), self.group.rect().height())
        event.accept()

    def mouseMoveEvent(self, event) -> None:
        delta = event.scenePos() - self._origin
        self.group.resize_to(self._initial_size[0] + delta.x(), self._initial_size[1] + delta.y())
        event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self.group.editor.mark_dirty()
        event.accept()


class LogicGroupItem(QGraphicsRectItem):
    """Comentário visual / grupo redimensionável para organizar blocos."""

    def __init__(self, editor: "LogicGraphEditor", group_data: dict) -> None:
        super().__init__()
        self.editor = editor
        self.group_data = group_data
        self.group_id = str(group_data.get("id", ""))
        position = group_data.get("position", [0.0, 0.0])
        size = group_data.get("size", [320.0, 240.0])
        self.setPos(float(position[0]), float(position[1]))
        self.setRect(0.0, 0.0, float(size[0]), float(size[1]))
        self.setZValue(-10)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setData(0, self.group_id)

        self.title_item = QGraphicsTextItem(str(group_data.get("title", "Grupo")), self)
        self.title_item.setDefaultTextColor(QColor("#d4e1f5"))
        self.title_item.setPos(8.0, 6.0)

        self.resize_handle = LogicGroupResizeHandle(self)
        self._apply_style()

    def _apply_style(self) -> None:
        color_hex = str(self.group_data.get("color", "#2d3545"))
        base_color = QColor(color_hex)
        base_color.setAlpha(65)
        self.setBrush(QBrush(base_color))
        border_color = QColor(color_hex).lighter(120)
        self.setPen(QPen(border_color, 2.0 if self.isSelected() else 1.2))
        self.resize_handle.setPos(
            self.rect().width() - self.resize_handle.SIZE - 4.0,
            self.rect().height() - self.resize_handle.SIZE - 4.0,
        )

    def resize_to(self, width: float, height: float) -> None:
        w = max(140.0, float(width))
        h = max(100.0, float(height))
        self.setRect(0.0, 0.0, w, h)
        self.group_data["size"] = [round(w, 2), round(h, 2)]
        self._apply_style()

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and hasattr(self, "editor"):
            from PySide6.QtCore import QPointF
            position = value if isinstance(value, QPointF) else self.pos()
            self.group_data["position"] = [round(position.x(), 2), round(position.y(), 2)]
            self.editor.mark_dirty()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self._apply_style()
        return result

    def mouseDoubleClickEvent(self, event) -> None:
        title, ok = QInputDialog.getText(
            None,
            "Editar Título do Grupo",
            "Título:",
            text=self.title_item.toPlainText(),
        )
        if ok and title.strip():
            self.title_item.setPlainText(title.strip())
            self.group_data["title"] = title.strip()
            self.editor.mark_dirty()
        event.accept()
