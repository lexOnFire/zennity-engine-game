"""Dockable Viewport for Graph Editor real-time preview."""
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt

class ViewportDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Viewport Preview", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Placeholder for the Phase 1 Viewport or isolated Runtime Manager
        self.play_btn = QPushButton("Play Isolated Runtime")
        layout.addWidget(self.play_btn)
        
        self.setWidget(container)
