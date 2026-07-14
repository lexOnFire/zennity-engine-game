"""Estado vazio reutilizável para painéis e diálogos do editor."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyStateWidget(QWidget):
    """Apresenta título e orientação sem acoplar o painel a uma paleta."""

    def __init__(self, title: str, description: str = "", glyph: str = "◇", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(5)
        layout.addStretch(1)

        icon = QLabel(glyph)
        icon.setObjectName("EmptyStateGlyph")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        heading = QLabel(title)
        heading.setObjectName("EmptyStateTitle")
        heading.setAlignment(Qt.AlignCenter)
        heading.setWordWrap(True)
        layout.addWidget(heading)

        if description:
            hint = QLabel(description)
            hint.setObjectName("EmptyStateDescription")
            hint.setAlignment(Qt.AlignCenter)
            hint.setWordWrap(True)
            layout.addWidget(hint)

        layout.addStretch(1)
