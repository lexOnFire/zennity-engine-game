from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class ConsoleDock(QDockWidget):
    """
    Painel acoplável do Console / Logs.
    Implementação básica (placeholder) da Semana 2.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Console", parent)
        self.setObjectName("ConsoleDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        
        label = QLabel("Console e Logs do Sistema\n[Implementação - Semana 8]")
        label.setStyleSheet("color: #828a9b;")
        
        layout.addWidget(label)
        layout.addStretch()
        
        self.setWidget(content)
