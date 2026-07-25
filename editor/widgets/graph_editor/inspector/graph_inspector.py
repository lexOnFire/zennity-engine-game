"""Data-driven Inspector for Graph Nodes."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata.node import NodeDefinition
from engine.localization import tr

class GraphInspector(QWidget):
    """Renders node properties dynamically based on their NodeDefinition metadata."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addStretch()
        
    def inspect(self, node_id: str):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        context = EngineContext.current()
        if not context: return
        manager = context.services.get_optional(MetadataManager)
        if not manager: return
        
        definition = manager.get(NodeDefinition, node_id)
        
        if not definition:
            return
            
        # Try to resolve localized string or fallback to definition value
        node_name = tr(definition.title_key, fallback=definition.title_key)
        category_name = tr(definition.category_key, fallback=definition.category_key)
        
        self.form_layout.addRow(QLabel(f"<b>{node_name}</b>"))
        self.form_layout.addRow(QLabel(f"<i>{category_name}</i>"))
        
        for pin in definition.inputs:
            pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=pin.label)
            self.form_layout.addRow(QLabel(pin_label), QLabel(f"[{pin.pin_type}]"))
