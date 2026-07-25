"""Auto-Documentation Generator."""
from engine.localization import tr

class AutoDocsGenerator:
    """Generates markdown documentation for nodes from Registry Metadata."""
    
    @staticmethod
    def generate_node_doc(node_id: str) -> str:
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition
        
        context = EngineContext.current()
        if not context:
            return tr("graph.documentation.not_found", fallback="Documentation not found.")
            
        manager = context.services.get_optional(MetadataManager)
        if not manager:
            return tr("graph.documentation.not_found", fallback="Documentation not found.")
            
        definition = manager.get(NodeDefinition, node_id)
        
        if not definition:
            return tr("graph.documentation.not_found", fallback="Documentation not found.")
            
        name = tr(definition.title_key, fallback=definition.title_key)
        desc = tr(definition.description_key, fallback=definition.description_key)
        cat = tr(definition.category_key, fallback=definition.category_key)
        
        md = f"# {name}\n\n"
        md += f"**Category:** {cat}\n\n"
        md += f"{desc}\n\n"
        md += "### Inputs\n"
        for pin in getattr(definition, "inputs", []):
            pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=getattr(pin, "title_key", pin.id))
            md += f"- **{pin_label}** (`{pin.pin_type}`)\n"
            
        md += "\n### Outputs\n"
        for pin in getattr(definition, "outputs", []):
            pin_label = tr(f"pin.{definition.id}.{pin.id}", fallback=getattr(pin, "title_key", pin.id))
            md += f"- **{pin_label}** (`{pin.pin_type}`)\n"
            
        if getattr(definition, "examples_key", ""):
            examples = tr(definition.examples_key, fallback="")
            if examples:
                md += f"\n### Examples\n{examples}\n"
                
        if getattr(definition, "best_practices_key", ""):
            bp = tr(definition.best_practices_key, fallback="")
            if bp:
                md += f"\n### Best Practices\n{bp}\n"
                
        if getattr(definition, "common_errors_key", ""):
            ce = tr(definition.common_errors_key, fallback="")
            if ce:
                md += f"\n### Common Errors\n{ce}\n"
            
        return md
