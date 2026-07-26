"""Dockable Viewport for Graph Editor real-time preview."""
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

class ViewportDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Viewport Preview", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.status_label = QLabel("Viewport aguardando conexão...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: gray; background-color: black;")
        
        self.play_btn = QPushButton("▶ Iniciar Teste Local")
        self.play_btn.setStyleSheet("background-color: #27ae60; color: white;")
        
        layout.addWidget(self.status_label, stretch=1)
        layout.addWidget(self.play_btn)
        
        self.setWidget(container)
