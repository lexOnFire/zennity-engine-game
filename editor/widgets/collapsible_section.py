from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

# Ícone por tipo de componente
_SECTION_ICONS: dict[str, str] = {
    "Transform": "⚡",
    "Mesh Renderer": "🔷",
    "Box Collider": "📦",
    "Circle Collider": "⭕",
    "RigidBody": "🔩",
    "Script": "📄",
}


class CollapsibleSection(QWidget):
    """Seção colapsável usada no Inspector – visual atualizado."""

    toggled = Signal(bool)
    reset_requested = Signal()

    def __init__(self, title: str, icon: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._is_expanded = True
        resolved_icon = icon or _SECTION_ICONS.get(title, "")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 6)
        outer.setSpacing(0)

        # ── Cabeçalho ────────────────────────────────────────────────
        self.header_widget = QWidget()
        self.header_widget.setObjectName("SectionHeader")
        self.header_widget.setStyleSheet(
            "#SectionHeader { background-color: #1b1e27; "
            "border: 1px solid #2a2d3a; border-radius: 6px; }"
        )
        hdr = QHBoxLayout(self.header_widget)
        hdr.setContentsMargins(8, 5, 8, 5)
        hdr.setSpacing(6)

        self.btn_toggle = QPushButton("▼")
        self.btn_toggle.setFixedSize(18, 18)
        self.btn_toggle.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "color: #6b7280; font-size: 9px; font-weight: bold; }"
            "QPushButton:hover { color: #9ca3af; }"
        )
        self.btn_toggle.clicked.connect(self.toggle_collapse)

        # Ícone opcional
        if resolved_icon:
            lbl_icon = QLabel(resolved_icon)
            lbl_icon.setStyleSheet("border: none; font-size: 13px;")
            hdr.addWidget(self.btn_toggle)
            hdr.addWidget(lbl_icon)
        else:
            hdr.addWidget(self.btn_toggle)

        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(
            "border: none; font-weight: 600; color: #d1d5db; font-size: 11px;"
        )
        hdr.addWidget(self.lbl_title)
        hdr.addStretch()

        # Botão reset ↻
        self.btn_reset = QPushButton("↻")
        self.btn_reset.setFixedSize(20, 20)
        self.btn_reset.setToolTip("Resetar para padrão")
        self.btn_reset.setStyleSheet(
            "QPushButton { background: transparent; border: none; "
            "color: #4b5563; font-size: 13px; }"
            "QPushButton:hover { color: #9ca3af; }"
        )
        self.btn_reset.clicked.connect(self.reset_requested)
        hdr.addWidget(self.btn_reset)

        outer.addWidget(self.header_widget)

        # ── Área de conteúdo ─────────────────────────────────────────
        self.content_widget = QWidget()
        self.content_widget.setObjectName("SectionContent")
        self.content_widget.setStyleSheet(
            "#SectionContent { background-color: #13151c; "
            "border: 1px solid #2a2d3a; border-top: none; "
            "border-bottom-left-radius: 6px; border-bottom-right-radius: 6px; }"
        )
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 8, 12, 10)
        self.content_layout.setSpacing(6)

        outer.addWidget(self.content_widget)

    def set_content_widget(self, widget: QWidget) -> None:
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.content_layout.addWidget(widget)

    @Slot()
    def toggle_collapse(self) -> None:
        self._is_expanded = not self._is_expanded
        self.content_widget.setVisible(self._is_expanded)
        self.btn_toggle.setText("▼" if self._is_expanded else "▶")
        self.toggled.emit(self._is_expanded)
