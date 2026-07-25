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
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition

        self.results.clear()
        context = EngineContext.current()
        if not context: return
        manager = context.services.get_optional(MetadataManager)
        if not manager: return

        nodes = manager.get_all(NodeDefinition)

        # Sort por categoria e título
        sorted_nodes = sorted(nodes, key=lambda n: (tr(getattr(n, "category_key", "General")), tr(getattr(n, "name_key", n.id))))

        for node in sorted_nodes:
            display_title = tr(getattr(node, "name_key", node.id))
            display_category = tr(getattr(node, "category_key", "General"))
            tags = getattr(node, "tags", [])
            search_blob = f"{display_title} {display_category} {node.id} {' '.join(tags)}".lower()

            item = QListWidgetItem(f"{display_title}  ({display_category})")
            item.setData(Qt.UserRole, node.id)
            item.setData(Qt.UserRole + 1, search_blob)
            self.results.addItem(item)

        if self.results.count() > 0:
            self.results.setCurrentRow(0)

    def _filter_nodes(self, text):
        search_text = text.lower().strip()
        for i in range(self.results.count()):
            item = self.results.item(i)
            search_blob = item.data(Qt.UserRole + 1) or item.text().lower()
            item.setHidden(bool(search_text) and (search_text not in search_blob))

        # Seleciona o primeiro visível
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
