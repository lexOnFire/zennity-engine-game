from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel


class HierarchyDock(QDockWidget):
    """
    Painel acoplável da Hierarquia de Objetos da Cena (Outliner).
    Implementação básica (placeholder) da Semana 2.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Hierarchy", parent)
        self.setObjectName("HierarchyDock")
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        
        label = QLabel("Hierarchy (Árvore de Objetos)\n[Implementação - Semana 3]")
        label.setStyleSheet("color: #828a9b;")
        
        layout.addWidget(label)
        layout.addStretch()
        
        self.setWidget(content)

# Importações necessárias adicionais
from PySide6.QtCore import Qt
