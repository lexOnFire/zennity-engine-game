from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class InspectorDock(QDockWidget):
    """
    Painel acoplável do Inspector (Propriedades dos Objetos).
    Implementação básica (placeholder) da Semana 2.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Inspector", parent)
        self.setObjectName("InspectorDock")
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        
        label = QLabel("Inspector (Componentes & Atributos)\n[Implementação - Semana 5]")
        label.setStyleSheet("color: #828a9b;")
        
        layout.addWidget(label)
        layout.addStretch()
        
        self.setWidget(content)
