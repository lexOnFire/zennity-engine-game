"""Dialogue Graph Editor Dock (2ª especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


class DialogueGraphEditorDock(QDockWidget):
    """Dock do Editor de Diálogos construído como 2ª especialização do GenericGraphEditorWidget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("💬 Dialogue Graph Editor", parent)
        self.setObjectName("DialogueGraphEditorDock")

        # Instancia o Editor Genérico filtrado para a categoria "Dialogue"
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="Dialogue", parent=self)
        self.setWidget(self.graph_editor)
