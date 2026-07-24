"""Universal Graph Registry for definitions and plugins."""
from typing import Any, Callable, Type
from engine.graphs.metadata.node import NodeDefinition
from engine.graphs.metadata.pin import PinDefinition

class GraphRegistry:
    """Singleton registry for all graph metadata, compilers and plugins."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_registry()
        return cls._instance
        
    def _init_registry(self):
        self._nodes: dict[str, NodeDefinition] = {}
        self._graph_types: dict[str, dict] = {}
        self._compilers: dict[str, Any] = {}
        self._serializers: dict[str, Any] = {}
        
    def register_node(self, definition: NodeDefinition) -> None:
        if definition.id in self._nodes:
            # Handle overrides or warnings later
            pass
        self._nodes[definition.id] = definition
        
    def get_node(self, node_id: str) -> NodeDefinition | None:
        return self._nodes.get(node_id)
        
    def get_all_nodes(self) -> list[NodeDefinition]:
        return list(self._nodes.values())
        
    def register_compiler(self, graph_type: str, compiler: Any) -> None:
        self._compilers[graph_type] = compiler
        
    def get_compiler(self, graph_type: str) -> Any | None:
        return self._compilers.get(graph_type)

    def register_serializer(self, graph_type: str, serializer: Any) -> None:
        self._serializers[graph_type] = serializer
        
    def get_serializer(self, graph_type: str) -> Any | None:
        return self._serializers.get(graph_type)


def register_node(**kwargs) -> Callable[[Type], Type]:
    """Decorator to register a node class with the Global Registry."""
    def decorator(cls: Type) -> Type:
        registry = GraphRegistry()
        
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
            best_practices=kwargs.get("best_practices", ""),
            common_errors=kwargs.get("common_errors", ""),
            runtime_class=cls
        )
        
        registry.register_node(definition)
        # Store definition on the class for reflection
        cls.__node_definition__ = definition
        
        return cls
    return decorator
