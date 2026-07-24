"""Ctrl+P Command Palette for quick access."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget
from PySide6.QtCore import Qt

class CommandPalette(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command or node name...")
        self.results = QListWidget()
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.results)
