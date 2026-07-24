"""Offline Documentation System for Graph Nodes."""
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLineEdit, QTextBrowser
from PySide6.QtCore import Qt

class DocumentationDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Documentation (Help)", parent)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes, events, functions...")
        
        self.doc_browser = QTextBrowser()
        self.doc_browser.setHtml("<h2>Zennity Documentation</h2><p>Search for a node to see its details, examples, and rules.</p>")
        
        layout.addWidget(self.search_bar)
        layout.addWidget(self.doc_browser)
        
        self.setWidget(container)
