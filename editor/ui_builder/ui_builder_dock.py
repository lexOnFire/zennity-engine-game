"""Dock do UI Builder da Zennity Engine (Fase 5 - Cliente da UI Platform)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QLineEdit,
    QSpinBox,
)

from engine.ui.runtime import UICanvas, UIPanel, UIButton, UILabel, UIImage


class UICanvasPreviewWidget(QWidget):
    """Canvas de visualização WYSIWYG de UI em tempo real."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.canvas_runtime = UICanvas("MainCanvas")
        self.selected_widget = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        painter.fillRect(rect, QColor("#121216"))

        # Renderiza a área do Canvas (800x450 proporção 16:9)
        cw, ch = 700, 394
        cx = (rect.width() - cw) // 2
        cy = (rect.height() - ch) // 2
        painter.fillRect(cx, cy, cw, ch, QColor("#1E1E26"))
        painter.setPen(QPen(QColor("#3A3A4C"), 2))
        painter.drawRect(cx, cy, cw, ch)

        # Renderiza os widgets filhos do Canvas
        for widget in self.canvas_runtime.children:
            wx = cx + int(widget.x)
            wy = cy + int(widget.y)
            ww = int(widget.width)
            wh = int(widget.height)

            if isinstance(widget, UIButton):
                painter.fillRect(wx, wy, ww, wh, QColor("#3498DB"))
                painter.setPen(QPen(QColor("#FFFFFF"), 1))
                painter.drawText(wx, wy, ww, wh, Qt.AlignCenter, getattr(widget, "text", "Button"))
            elif isinstance(widget, UILabel):
                painter.setPen(QPen(QColor("#2ECC71"), 1))
                painter.drawText(wx, wy, ww, wh, Qt.AlignLeft | Qt.AlignVCenter, getattr(widget, "text", "Label"))
            elif isinstance(widget, UIPanel):
                painter.fillRect(wx, wy, ww, wh, QColor("#2C3E50"))


class UIBuilderDock(QDockWidget):
    """Dock do UI Builder Visual (Cliente oficial da UI Platform)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🎨 UI Builder", parent)
        self.setObjectName("UIBuilderDock")

        container = QWidget(self)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Toolbar Superior
        toolbar = QHBoxLayout()
        btn_add_panel = QPushButton("+ Panel", self)
        btn_add_panel.clicked.connect(lambda: self.add_widget(UIPanel("Panel_1")))

        btn_add_button = QPushButton("+ Button", self)
        btn_add_button.clicked.connect(lambda: self.add_widget(UIButton("Button_1")))

        btn_add_label = QPushButton("+ Label", self)
        btn_add_label.clicked.connect(lambda: self.add_widget(UILabel("Label_1")))

        toolbar.addWidget(QLabel("UI Widgets:", self))
        toolbar.addWidget(btn_add_panel)
        toolbar.addWidget(btn_add_button)
        toolbar.addWidget(btn_add_label)
        toolbar.addStretch(1)
        main_layout.addLayout(toolbar)

        # Splitter (Hierarquia | Canvas | Inspector)
        splitter = QSplitter(Qt.Horizontal, container)

        # 1. Painel de Hierarquia
        self.tree_hierarchy = QTreeWidget(splitter)
        self.tree_hierarchy.setHeaderLabel("Hierarquia de UI")
        splitter.addWidget(self.tree_hierarchy)

        # 2. Preview Canvas WYSIWYG
        self.preview_canvas = UICanvasPreviewWidget(splitter)
        splitter.addWidget(self.preview_canvas)

        # 3. Painel de Propriedades (Inspector)
        self.inspector_panel = QWidget(splitter)
        insp_layout = QVBoxLayout(self.inspector_panel)
        insp_layout.addWidget(QLabel("Propriedades do Widget", self))
        self.txt_name = QLineEdit(self)
        insp_layout.addWidget(QLabel("Nome:", self))
        insp_layout.addWidget(self.txt_name)
        insp_layout.addStretch(1)
        splitter.addWidget(self.inspector_panel)

        splitter.setSizes([180, 500, 200])
        main_layout.addWidget(splitter, 1)
        self.setWidget(container)

        self.rebuild_hierarchy_tree()

    def rebuild_hierarchy_tree(self) -> None:
        self.tree_hierarchy.clear()
        root_item = QTreeWidgetItem(self.tree_hierarchy, [self.preview_canvas.canvas_runtime.name])
        for child in self.preview_canvas.canvas_runtime.children:
            QTreeWidgetItem(root_item, [child.name])
        self.tree_hierarchy.expandAll()

    def add_widget(self, widget) -> None:
        self.preview_canvas.canvas_runtime.add_child(widget)
        self.rebuild_hierarchy_tree()
        self.preview_canvas.update()
