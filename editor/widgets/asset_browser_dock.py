from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class AssetBrowserDock(QDockWidget):
    """
    Painel acoplável do Asset Browser (Navegador de Recursos).
    Implementação básica (placeholder) da Semana 2.
    """
    
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Recursos", parent)
        self.setObjectName("AssetBrowserDock")
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Conteúdo interno
        content = QWidget()
        layout = QVBoxLayout(content)
        
        label = QLabel("Asset Browser (Recursos do Projeto)\n[Implementação - Semana 4]")
        label.setStyleSheet("color: #828a9b;")
        
        layout.addWidget(label)
        layout.addStretch()
        
        self.setWidget(content)
