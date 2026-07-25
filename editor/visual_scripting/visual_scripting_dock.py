"""Visual Scripting Editor Dock (4ª especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


class VisualScriptingEditorDock(QDockWidget):
    """Dock do Editor de Scripting Visual completo (Logic Graph Editor com Conexões, Blackboard, Receitas e Nós)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("⚡ Visual Scripting Editor", parent)
        self.setObjectName("VisualScriptingEditorDock")

        # Instancia o Editor Completo de Grafos de Lógica Visual (LogicGraphEditor)
        from editor.widgets.logic_graph_editor import LogicGraphEditor
        self.graph_editor = LogicGraphEditor(parent=self)
        self.setWidget(self.graph_editor)
