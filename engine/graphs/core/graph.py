"""Generic Graph base class and registry."""

from __future__ import annotations

from typing import Any, Mapping

from engine.graphs.core.node import GraphNode
from engine.graphs.core.connection import GraphConnection


class Graph:
    """Classe base genérica para todo grafo criado na Zennity Engine."""
    
    graph_name = "Generic Graph"
    graph_icon = "graph"
    graph_color = "#ffffff"
    
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.connections: list[GraphConnection] = []
        self.properties: dict[str, Any] = {}
        
    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        
    def remove_node(self, node_id: str) -> None:
        if node_id in self.nodes:
            self._remove_connections_for_node(node_id)
            del self.nodes[node_id]
            
    def _remove_connections_for_node(self, node_id: str) -> None:
        self.connections = [
            c for c in self.connections 
            if c.from_node.id != node_id and c.to_node.id != node_id
        ]
        
    def add_connection(self, connection: GraphConnection) -> None:
        self.connections.append(connection)
        
    def remove_connection(self, connection_id: str) -> None:
        self.connections = [c for c in self.connections if c.id != connection_id]

    def serialize(self) -> dict[str, Any]:
        return {
            "graph_type": self.__class__.__name__,
            "properties": self.properties.copy(),
            "nodes": [node.serialize() for node in self.nodes.values()],
            "connections": [conn.serialize() for conn in self.connections],
        }

    # Nota: A desserialização exigirá um NodeRegistry para instanciar as subclasses corretas de GraphNode.
