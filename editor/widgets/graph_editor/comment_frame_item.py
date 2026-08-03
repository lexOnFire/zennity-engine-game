"""CommentFrameItem — Caixa de Grupo e Comentários para Editores de Grafos (Fase UX Graph Editors).

Permite criar frames/caixas de comentários coloridos para agrupar e organizar nós.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import QGraphicsRectItem


class CommentFrameItem(QGraphicsRectItem):
    """Item gráfico para agrupamento visual e comentários de nós no canvas."""

    def __init__(
        self,
        title: str = "Novo Grupo de Nós",
        rect: QRectF = QRectF(0, 0, 300, 200),
        color_hex: str = "#2C3E50",
        parent=None,
    ):
        super().__init__(rect, parent)
        self.title = title
        self.color_hex = color_hex
        self.setFlags(
            QGraphicsRectItem.ItemIsMovable
            | QGraphicsRectItem.ItemIsSelectable
            | QGraphicsRectItem.ItemSendsGeometryChanges
        )
        self.setZValue(-10.0)  # Fica ao fundo dos nós

    def paint(self, painter, option, widget=None):
        rect = self.boundingRect()

        # Fundo semi-transparente
        bg_color = QColor(self.color_hex)
        bg_color.setAlpha(60)
        painter.setBrush(bg_color)

        border_color = QColor(self.color_hex).lighter(130)
        painter.setPen(QPen(border_color, 2, Qt.DashLine if not self.isSelected() else Qt.SolidLine))
        painter.drawRoundedRect(rect, 8.0, 8.0)

        # Cabeçalho do comentário
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), 30)
        header_bg = QColor(self.color_hex)
        header_bg.setAlpha(180)
        painter.fillRect(header_rect, header_bg)

        # Texto do título
        painter.setPen(Qt.white)
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(header_rect.adjusted(10, 0, 0, 0), Qt.AlignVCenter | Qt.AlignLeft, self.title)
