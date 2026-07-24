"""Public API for developers."""
from typing import Type, Callable, Any
from engine.graphs.registry.graph_registry import GraphRegistry
from engine.core.metadata import NodeDefinition, GraphDefinition, CategoryDefinition

# --- Imperative API ---
def register_compiler(graph_id: str, compiler: Any) -> None:
    GraphRegistry().register_compiler(graph_id, compiler)

def register_serializer(graph_id: str, serializer: Any) -> None:
    GraphRegistry().register_serializer(graph_id, serializer)

# --- Declarative API (Decorators) ---
def register_node(**kwargs) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        definition = NodeDefinition(
            id=kwargs.get("id", f"{cls.__module__}.{cls.__name__}"),
            name=kwargs.get("name", cls.__name__),
            category=kwargs.get("category", "Uncategorized"),
            description=kwargs.get("description", ""),
            color=kwargs.get("color", "#808080"),
            icon=kwargs.get("icon", ""),
            keywords=kwargs.get("keywords", []),
            tags=kwargs.get("tags", []),
            version=kwargs.get("version", "1.0.0"),
            author=kwargs.get("author", "Zennity"),
            inputs=kwargs.get("inputs", []),
            outputs=kwargs.get("outputs", []),
            examples=kwargs.get("examples", ""),
            runtime_class=cls
        )
        GraphRegistry().register_node(definition)
        cls.__node_definition__ = definition
        return cls
    return decorator

def register_graph(**kwargs) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        definition = GraphDefinition(
            id=kwargs.get("id", cls.__name__.lower()),
            name=kwargs.get("name", cls.__name__),
            description=kwargs.get("description", ""),
            icon=kwargs.get("icon", ""),
            color=kwargs.get("color", "#444444"),
            extension=kwargs.get("extension", ".zgraph")
        )
        GraphRegistry().register_graph(definition)
        cls.__graph_definition__ = definition
        return cls
    return decorator
