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
        
        header = QWidget()
        header.setObjectName("PanelHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(8, 4, 8, 4)
        label = QLabel(title)
        label.setObjectName("PanelHeaderTitle")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(QLabel("gear x"))
        self.setTitleBarWidget(header)
