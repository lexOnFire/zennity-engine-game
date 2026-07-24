"""Graph System Registry for types and nodes."""

from __future__ import annotations

from typing import Type

from engine.graphs.core.graph import Graph
from engine.graphs.core.node import GraphNode


class GraphRegistry:
    """Singleton para registrar tipos de grafos e seus nós permitidos na engine."""
    
    _graph_types: dict[str, Type[Graph]] = {}
    _node_types: dict[str, dict[str, Type[GraphNode]]] = {}
    
    @classmethod
    def register_graph_type(cls, graph_class: Type[Graph]) -> None:
        name = graph_class.__name__
        cls._graph_types[name] = graph_class
        if name not in cls._node_types:
            cls._node_types[name] = {}
            
    @classmethod
    def register_node_for_graph(cls, graph_name: str, node_class: Type[GraphNode]) -> None:
        if graph_name not in cls._node_types:
            cls._node_types[graph_name] = {}
        cls._node_types[graph_name][node_class.__name__] = node_class

    @classmethod
    def get_graph_class(cls, name: str) -> Type[Graph] | None:
        return cls._graph_types.get(name)
        
    @classmethod
    def get_node_class(cls, graph_name: str, node_name: str) -> Type[GraphNode] | None:
        return cls._node_types.get(graph_name, {}).get(node_name)

def register_graph(cls: Type[Graph]) -> Type[Graph]:
    """Decorator para registrar um Graph."""
    GraphRegistry.register_graph_type(cls)
    return cls

def register_node(graph_name: str):
    """Decorator para registrar um Node em um Graph específico."""
    def decorator(cls: Type[GraphNode]) -> Type[GraphNode]:
        GraphRegistry.register_node_for_graph(graph_name, cls)
        return cls
    return decorator
