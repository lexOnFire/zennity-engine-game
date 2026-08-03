"""Dock do Visualizador de Dependências de Assets (Dependency Viewer Dock)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from engine.assets.dependency_graph import AssetDependencyGraph


class DependencyViewerDock(QDockWidget):
    """Dock para visualização do Grafo de Dependências entre Assets e Cenas."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🔗 Asset Dependency Viewer", parent)
        self.setObjectName("DependencyViewerDock")

        self.dep_graph = AssetDependencyGraph()

        # Reutiliza a Plataforma de Grafos Genérica
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="", parent=self)
        self.graph_editor.label_title.setText("🔗 Asset Dependency Graph")
        self.setWidget(self.graph_editor)
