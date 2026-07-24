from .graph_registry import GraphRegistry
from engine.core.metadata import NodeDefinition

def register_node(**kwargs):
    def decorator(cls):
        # Backwards compatibility mapping for localization keys
        if "name" in kwargs:
            kwargs["name_key"] = kwargs.pop("name")
        if "category" in kwargs:
            kwargs["category_key"] = kwargs.pop("category")
        if "description" in kwargs:
            kwargs["description_key"] = kwargs.pop("description")
            
        # Creates a node definition from kwargs and binds the class implementation
        definition = NodeDefinition(**kwargs)
        definition.runtime_class = cls
        
        # Register in the singleton registry
        GraphRegistry().register_node(definition)
        return cls
    return decorator

__all__ = ["GraphRegistry", "register_node"]
