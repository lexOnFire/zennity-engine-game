"""
editor/inspector/collapsible_card.py
─────────────────────────────────────────────────────────────────────────────
Card de Componente Recolhível (Collapsible Header Card estilo Unity).
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QCheckBox, QFrame, QMenu
)
from PySide6.QtGui import QIcon, QAction


class CollapsibleComponentCard(QFrame):
    """Card retrátil com header expansível, checkbox de ativação e menu de opções."""

    toggled = Signal(bool)
    removed = Signal()

    def __init__(self, title: str, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            CollapsibleComponentCard {
                background-color: #1e222b;
                border: 1px solid #2d3340;
                border-radius: 6px;
                margin-bottom: 6px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header ───────────────────────────────────────────────────────────
        header_widget = QWidget(self)
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #262b36;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 4, 8, 4)

        # Toggle Expand/Collapse Button
        self.toggle_btn = QToolButton(header_widget)
        self.toggle_btn.setArrowType(Qt.DownArrow)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setStyleSheet("border: none; background: transparent; color: #a0aab8;")
        self.toggle_btn.clicked.connect(self._toggle_content)
        header_layout.addWidget(self.toggle_btn)

        # Active Checkbox
        self.active_chk = QCheckBox(header_widget)
        self.active_chk.setChecked(True)
        self.active_chk.toggled.connect(self.toggled.emit)
        header_layout.addWidget(self.active_chk)

        # Title Label
        self.title_lbl = QLabel(f"<b>{title}</b>", header_widget)
        self.title_lbl.setStyleSheet("color: #ffffff; font-size: 12px;")
        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()

        # Options Menu Button (...)
        self.menu_btn = QToolButton(header_widget)
        self.menu_btn.setText("⋮")
        self.menu_btn.setStyleSheet("border: none; background: transparent; color: #ffffff; font-weight: bold;")
        self.menu_btn.clicked.connect(self._show_options_menu)
        header_layout.addWidget(self.menu_btn)

        main_layout.addWidget(header_widget)

        # ── Body Content ──────────────────────────────────────────────────────
        self.body_widget = QWidget(self)
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.addWidget(self.body_widget)

    def _toggle_content(self, checked: bool) -> None:
        self.toggle_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.body_widget.setVisible(checked)

    def _show_options_menu(self) -> None:
        menu = QMenu(self)
        remove_act = QAction("Remover Componente", self)
        remove_act.triggered.connect(self.removed.emit)
        menu.addAction(remove_act)
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    def add_widget(self, widget: QWidget) -> None:
        self.body_layout.addWidget(widget)
