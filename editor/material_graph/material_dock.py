"""Material Graph Editor Dock (3ª especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


class MaterialGraphEditorDock(QDockWidget):
    """Dock do Editor de Materiais e Shaders construído como 3ª especialização do GenericGraphEditorWidget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🎨 Material Graph Editor", parent)
        self.setObjectName("MaterialGraphEditorDock")

        # Instancia o Editor Genérico filtrado para a categoria "Material"
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="Material", parent=self)
        self.setWidget(self.graph_editor)
