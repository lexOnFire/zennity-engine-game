"""Command Palette for searching and instantiating graph nodes."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from engine.localization.manager import tr

class CommandPaletteWidget(QDialog):
    node_selected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Nó")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setFixedSize(300, 400)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2d31;
                border: 1px solid #1e1f22;
                border-radius: 6px;
            }
            QLineEdit {
                background-color: #1e1f22;
                color: #dcddde;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                color: #dcddde;
                outline: 0;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #404249;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar nó...")
        self.search_input.textChanged.connect(self._filter_nodes)
        
        self.results = QListWidget()
        self.results.itemActivated.connect(self._on_item_activated)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.results)
        
    def show_at(self, global_pos):
        self.move(global_pos)
        self.search_input.clear()
        self._populate_all()
        self.show()
        self.search_input.setFocus()
        
    def _populate_all(self):
        from engine.graphs.registry import GraphRegistry
        self.results.clear()
        nodes = GraphRegistry.get_all_nodes()
        
        # Sort by category and name
        sorted_nodes = sorted(nodes.values(), key=lambda n: (tr(n.category_key), tr(n.name_key)))
        
        for node in sorted_nodes:
            item = QListWidgetItem(f"{tr(node.name_key)}  ({tr(node.category_key)})")
            item.setData(Qt.UserRole, node.id)
            self.results.addItem(item)
            
        if self.results.count() > 0:
            self.results.setCurrentRow(0)
            
    def _filter_nodes(self, text):
        search_text = text.lower()
        for i in range(self.results.count()):
            item = self.results.item(i)
            item.setHidden(search_text not in item.text().lower())
            
        # Select first visible
        for i in range(self.results.count()):
            if not self.results.item(i).isHidden():
                self.results.setCurrentRow(i)
                break
                
    def _on_item_activated(self, item):
        node_id = item.data(Qt.UserRole)
        self.node_selected.emit(node_id)
        self.hide()
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            item = self.results.currentItem()
            if item and not item.isHidden():
                self._on_item_activated(item)
        elif event.key() == Qt.Key_Down:
            self.results.setFocus()
            super().keyPressEvent(event)
        elif event.key() == Qt.Key_Up:
            self.results.setFocus()
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
