"""Behavior Tree Editor Dock (Especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


class BehaviorTreeEditorDock(QDockWidget):
    """Dock do Editor de Behavior Tree especializado a partir do GenericGraphEditorWidget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🧠 Behavior Tree Editor", parent)
        self.setObjectName("BehaviorTreeEditorDock")

        # Instancia o Editor de Grafos Genérico filtrado para "Behavior Tree"
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree", parent=self)
        self.setWidget(self.graph_editor)
