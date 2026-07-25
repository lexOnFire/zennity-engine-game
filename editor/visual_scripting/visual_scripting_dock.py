"""Visual Scripting Editor Dock (4ª especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


class VisualScriptingEditorDock(QDockWidget):
    """Dock do Editor de Scripting Visual construído como 4ª especialização do GenericGraphEditorWidget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("⚡ Visual Scripting Editor", parent)
        self.setObjectName("VisualScriptingEditorDock")

        # Instancia o Editor Genérico filtrado para a categoria "Visual Scripting"
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="Visual Scripting", parent=self)
        self.setWidget(self.graph_editor)
