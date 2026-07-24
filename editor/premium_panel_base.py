from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QHBoxLayout, QLabel

class Panel(QDockWidget):
    def __init__(self, title: str) -> None:
        super().__init__(title)
        self.setObjectName("PremiumPanel")
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setWidget(self.container)
        
        # O custom title bar foi removido para permitir o uso da title bar padrão
        # do QDockWidget, que possui os botões Float e Close essenciais.
