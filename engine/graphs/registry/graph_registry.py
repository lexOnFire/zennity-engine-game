"""Universal Robust Graph Registry."""
from typing import Any, Type, Callable
from engine.core.metadata import NodeDefinition, GraphDefinition, CategoryDefinition

class GraphRegistry:
    """Singleton registry for EVERYTHING in the Graph Framework."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_registry()
        return cls._instance
        
    def _init_registry(self):
        self._nodes: dict[str, NodeDefinition] = {}
        self._graphs: dict[str, GraphDefinition] = {}
        self._categories: dict[str, CategoryDefinition] = {}
        self._compilers: dict[str, Any] = {}
        self._serializers: dict[str, Any] = {}
        self._plugins: set[str] = set()
        
    # --- Nodes ---
    def register_node(self, definition: NodeDefinition) -> None:
        self._nodes[definition.id] = definition
        
    def get_node(self, node_id: str) -> NodeDefinition | None:
        return self._nodes.get(node_id)
        
    def get_all_nodes(self) -> list[NodeDefinition]:
        return list(self._nodes.values())
        
    # --- Graphs ---
    def register_graph(self, definition: GraphDefinition) -> None:
        self._graphs[definition.id] = definition
        
    def get_graph(self, graph_id: str) -> GraphDefinition | None:
        return self._graphs.get(graph_id)
        
    # --- Categories ---
    def register_category(self, definition: CategoryDefinition) -> None:
        self._categories[definition.id] = definition
        
    # --- Framework Modules ---
    def register_compiler(self, graph_id: str, compiler: Any) -> None:
        self._compilers[graph_id] = compiler
        
    def register_serializer(self, graph_id: str, serializer: Any) -> None:
        self._serializers[graph_id] = serializer
        
    def get_compiler(self, graph_id: str) -> Any | None:
        return self._compilers.get(graph_id)
