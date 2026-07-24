"""Auto-Documentation Generator."""
from engine.graphs.registry.graph_registry import GraphRegistry
from engine.localization import tr

class AutoDocsGenerator:
    """Generates markdown documentation for nodes from Registry Metadata."""
    
    @staticmethod
    def generate_node_doc(node_id: str) -> str:
        registry = GraphRegistry()
        definition = registry.get_node(node_id)
        
        if not definition:
            return tr("graph.documentation.not_found", fallback="Documentation not found.")
            
        name = tr(f"node.{definition.id}.name", fallback=definition.name)
        desc = tr(f"node.{definition.id}.desc", fallback=definition.description)
        cat = tr(f"graph.category.{definition.category.lower()}", fallback=definition.category)
        
        md = f"# {name}\n\n"
        md += f"**Category:** {cat}\n\n"
        md += f"{desc}\n\n"
        md += "### Inputs\n"
        for pin in definition.inputs:
            pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=pin.label)
            md += f"- **{pin_label}** (`{pin.pin_type}`)\n"
            
        md += "\n### Outputs\n"
        for pin in definition.outputs:
            pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=pin.label)
            md += f"- **{pin_label}** (`{pin.pin_type}`)\n"
            
        return md
