"""Offline Documentation System for Graph Nodes."""
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QLineEdit, QTextBrowser
from PySide6.QtCore import Qt

class DocumentationDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("📖 Documentation (F1)", parent)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes, events, functions...")
        
        self.doc_browser = QTextBrowser()
        self.doc_browser.setHtml(
            "<h2>Zennity Documentation</h2>"
            "<p>Busque por nós ou tópicos da API interna.</p>"
            "<p><i>O sistema de tradução inteligente (i18n) está ativo.</i></p>"
        )
        
        layout.addWidget(self.search_bar)
        layout.addWidget(self.doc_browser)
        
        self.setWidget(container)