"""Workspace visual para criar e editar assets ``.zlogic``."""

from __future__ import annotations

import json
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, TYPE_CHECKING

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

if TYPE_CHECKING:
    from editor.widgets.logic_graph_editor import LogicGraphEditor

class LogicGraphView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, editor: "LogicGraphEditor", parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.editor = editor
        self.setObjectName("LogicGraphView")
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setStyleSheet(
            "QGraphicsView#LogicGraphView {"
            "background: #12141c; border: 1px solid #1f2430; border-radius: 6px;"
            "}"
        )

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        painter.fillRect(rect, QColor("#12141c"))
        spacing = 24
        left = int(rect.left()) - (int(rect.left()) % spacing)
        top = int(rect.top()) - (int(rect.top()) % spacing)
        painter.setPen(QPen(QColor("#181b24"), 1))
        for x in range(left, int(rect.right()) + spacing, spacing):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()) + spacing, spacing):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

        major = spacing * 5
        major_left = int(rect.left()) - (int(rect.left()) % major)
        major_top = int(rect.top()) - (int(rect.top()) % major)
        painter.setPen(QPen(QColor("#212533"), 1))
        for x in range(major_left, int(rect.right()) + major, major):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(major_top, int(rect.bottom()) + major, major):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.12 if event.angleDelta().y() > 0 else 1 / 1.12
            self.scale(factor, factor)
            event.accept()
            return
        super().wheelEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if event.modifiers() & Qt.ShiftModifier:
                self.editor.redo()
            else:
                self.editor.undo()
            event.accept()
            return
        if event.key() == Qt.Key_Y and event.modifiers() & Qt.ControlModifier:
            self.editor.redo()
            event.accept()
            return
        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            self.editor.duplicate_selected()
            event.accept()
            return
        if event.key() == Qt.Key_C and event.modifiers() & Qt.ControlModifier:
            self.editor.copy_selected()
            event.accept()
            return
        if event.key() == Qt.Key_X and event.modifiers() & Qt.ControlModifier:
            self.editor.cut_selected()
            event.accept()
            return
        if event.key() == Qt.Key_V and event.modifiers() & Qt.ControlModifier:
            self.editor.paste_selected()
            event.accept()
            return
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.editor.delete_selected()
            event.accept()
            return
        if event.key() == Qt.Key_C and not (event.modifiers() & Qt.ControlModifier):
            if hasattr(self.editor, "add_comment_box"):
                self.editor.add_comment_box()
            event.accept()
            return
        if event.key() == Qt.Key_F and (event.modifiers() & Qt.ShiftModifier or event.modifiers() & Qt.ControlModifier):
            if hasattr(self.editor, "auto_arrange_nodes"):
                self.editor.auto_arrange_nodes()
            event.accept()
            return
        if event.key() == Qt.Key_Escape:
            self.editor.cancel_connection()
            event.accept()
            return
        super().keyPressEvent(event)

class LogicMiniMapView(QGraphicsView):
    """Visão geral compacta; clicar recentraliza o canvas principal."""

    def __init__(self, scene: QGraphicsScene, editor: "LogicGraphEditor") -> None:
        super().__init__(scene)
        self.editor = editor
        self.setObjectName("LogicMiniMap")
        self.setFixedSize(190, 120)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setStyleSheet("border: 1px solid #454a56; background: #111318;")

    def refresh(self) -> None:
        bounds = self.scene().itemsBoundingRect().adjusted(-60.0, -60.0, 60.0, 60.0)
        if not bounds.isEmpty():
            self.fitInView(bounds, Qt.KeepAspectRatio)

    def mousePressEvent(self, event) -> None:
        self.editor.view.centerOn(self.mapToScene(event.position().toPoint()))
        event.accept()

