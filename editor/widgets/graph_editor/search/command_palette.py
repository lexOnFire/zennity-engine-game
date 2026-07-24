"""Command Palette Widget."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from .universal_search import UniversalSearchProvider

class CommandPalette(QDialog):
    """A Ctrl+P style universal search palette."""
    
    item_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search nodes, assets, commands...")
        self.search_input.textChanged.connect(self._on_search)
        
        self.results_list = QListWidget()
        self.results_list.itemActivated.connect(self._on_item_activated)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.results_list)
        
        self._current_results = []
        
    def _on_search(self, text: str):
        self.results_list.clear()
        if not text:
            return
            
        self._current_results = UniversalSearchProvider.query(text)
        for res in self._current_results:
            item = QListWidgetItem(f"{res['name']} ({res['category']})")
            item.setToolTip(res["description"])
            self.results_list.addItem(item)
            
    def _on_item_activated(self, item: QListWidgetItem):
        idx = self.results_list.row(item)
        if 0 <= idx < len(self._current_results):
            self.item_selected.emit(self._current_results[idx])
            self.accept()
