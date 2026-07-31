"""Material Graph Editor Dock (3ª especialização do GenericGraphEditorWidget)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QSplitter
from PySide6.QtCore import Qt
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.material_graph.preview_widget import MaterialPreviewWidget
from engine.graphics.material_graph import MaterialGraph


class MaterialGraphEditorDock(QDockWidget):
    """Dock do Editor de Materiais e Shaders construído como 3ª especialização do GenericGraphEditorWidget."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🎨 Material Graph Editor", parent)
        self.setObjectName("MaterialGraphEditorDock")

        self.splitter = QSplitter(Qt.Horizontal, self)
        
        # Instancia o Editor Genérico filtrado para a categoria "Material"
        self.graph_editor = GenericGraphEditorWidget(graph_category_filter="Material", parent=self)
        
        # Instancia o Widget de Preview GLSL
        self.preview_widget = MaterialPreviewWidget(parent=self)
        
        self.splitter.addWidget(self.graph_editor)
        self.splitter.addWidget(self.preview_widget)
        
        # Define proporções iniciais
        self.splitter.setSizes([700, 300])

        self.setWidget(self.splitter)
        
        # Conecta eventos de compilação
        self.graph_editor.canvas.asset_changed.connect(self._recompile_shader)
        self.graph_editor.document_changed.connect(lambda _: self._recompile_shader())
        
    def _recompile_shader(self) -> None:
        """Recompila o grafo material e atualiza o shader no preview."""
        try:
            # Pega o dicionário raw da canvas
            graph_data = self.graph_editor.graph_data()
            if not graph_data.get("nodes"):
                return
            
            # Testa a estrutura básica antes de instanciar para evitar ValueError
            # Só recompila se tiver ao menos um nó material.pbr_output
            has_output = any(n.get("type") == "material.pbr_output" for n in graph_data.get("nodes", []))
            if not has_output:
                return

            material = MaterialGraph(graph_data)
            glsl_data = material.compile_glsl()
            
            if glsl_data.get("backend") == "opengl":
                self.preview_widget.set_shader(glsl_data["fragment"], glsl_data.get("uniforms", {}))
                
        except Exception as e:
            # Se houver erros (grafo incompleto), ignorar para evitar spam no console durante a edição.
            pass
