from PySide6.QtWidgets import QFrame, QVBoxLayout, QWidget, QHBoxLayout, QLabel

class Panel(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("PremiumPanel")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        header = QWidget()
        header.setObjectName("PanelHeader")
        row = QHBoxLayout(header)
        row.setContentsMargins(8, 4, 8, 4)
        label = QLabel(title)
        label.setObjectName("PanelHeaderTitle")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(QLabel("gear x"))
        self.layout.addWidget(header)
