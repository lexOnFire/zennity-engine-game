"""Data-driven Inspector for Graph Nodes."""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout
from engine.graphs.registry import GraphRegistry

class GraphInspector(QWidget):
    """Renders node properties dynamically based on their NodeDefinition metadata."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addStretch()
        
    def inspect(self, node_id: str):
        # Clear previous
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        registry = GraphRegistry()
        definition = registry.get_node(node_id)
        
        if not definition:
            self.form_layout.addRow(QLabel("No node selected or unknown node."))
            return
            
        self.form_layout.addRow(QLabel(f"<b>{definition.name}</b>"))
        self.form_layout.addRow(QLabel(f"<i>{definition.category}</i>"))
        self.form_layout.addRow(QLabel(definition.description))
        self.form_layout.addRow(QLabel(f"Author: {definition.author} (v{definition.version})"))
        
        self.form_layout.addRow(QLabel("<b>Inputs</b>"))
        for pin in definition.inputs:
            self.form_layout.addRow(QLabel(pin.label), QLabel(f"[{pin.pin_type}]"))
            
        self.form_layout.addRow(QLabel("<b>Outputs</b>"))
        for pin in definition.outputs:
            self.form_layout.addRow(QLabel(pin.label), QLabel(f"[{pin.pin_type}]"))
