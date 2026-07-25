"""Public API for developers."""
from typing import Type, Callable, Any
from engine.core.metadata import NodeDefinition, GraphDefinition, CategoryDefinition

# Compilers and serializers will be registered during boot or via context now.
# Imperative API can be deprecated or refactored to use MetadataManager via EngineContext.
def register_compiler(graph_id: str, compiler: Any) -> None:
    pass # Deprecated for global static access. 

def register_serializer(graph_id: str, serializer: Any) -> None:
    pass # Deprecated for global static access.

# --- Declarative API (Decorators) ---
def register_node(**kwargs) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        definition = NodeDefinition(
            id=kwargs.get("id", f"{cls.__module__}.{cls.__name__}"),
            title_key=kwargs.get("name", cls.__name__),
            category_key=kwargs.get("category", "Uncategorized"),
            description_key=kwargs.get("description", ""),
            icon=kwargs.get("icon", ""),
            tags=kwargs.get("tags", []),
            version=kwargs.get("version", "1.0.0"),
            inputs=kwargs.get("inputs", []),
            outputs=kwargs.get("outputs", [])
        )
        # Store runtime class in definition for later instantiation
        definition._node_class = cls
        cls.__node_definition__ = definition
        return cls
    return decorator

def register_graph(**kwargs) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        definition = GraphDefinition(
            id=kwargs.get("id", cls.__name__.lower()),
            title_key=kwargs.get("name", cls.__name__),
            description_key=kwargs.get("description", ""),
            icon=kwargs.get("icon", ""),
        )
        definition._graph_class = cls
        cls.__graph_definition__ = definition
        return cls
    return decorator
