"""Graph Serialization and Deserialization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.graphs.core.graph import Graph
from engine.graphs.core.node import GraphNode
from engine.graphs.core.connection import GraphConnection
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.core.metadata import GraphDefinition, NodeDefinition

class GraphSerializer:
    """Sistema modular de I/O para arquivos .zgraph."""
    
    @classmethod
    def save(cls, graph: Graph, filepath: Path) -> None:
        data = graph.serialize()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
    @classmethod
    def load(cls, filepath: Path) -> Graph:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        context = EngineContext.current()
        manager = context.services.get(MetadataManager)
            
        graph_type_name = data.get("graph_type", "Generic Graph").lower()
        g_def = manager.get(GraphDefinition, graph_type_name)
        if not g_def or not hasattr(g_def, "_graph_class"):
            raise ValueError(f"Tipo de grafo não registrado na engine: {graph_type_name}")
            
        graph = g_def._graph_class()
        graph.properties = data.get("properties", {}).copy()
        
        # Load Nodes
        for node_data in data.get("nodes", []):
            node_type = node_data.get("type")
            n_def = manager.get(NodeDefinition, node_type)
            if not n_def or not hasattr(n_def, "_node_class"):
                print(f"Warning: Nó não encontrado no registro para '{graph_type_name}': {node_type}")
                continue
                
            node_class = n_def._node_class
                
            node = node_class(node_id=node_data.get("id"))
            node.deserialize(node_data)
            graph.add_node(node)
            
        # Load Connections
        for conn_data in data.get("connections", []):
            from_node = graph.nodes.get(conn_data.get("from_node"))
            to_node = graph.nodes.get(conn_data.get("to_node"))
            
            if not from_node or not to_node:
                continue
                
            from_pin = from_node.get_output(conn_data.get("from_pin"))
            to_pin = to_node.get_input(conn_data.get("to_pin"))
            
            if from_pin and to_pin:
                conn = GraphConnection(from_node, from_pin, to_node, to_pin)
                conn.id = conn_data.get("id", conn.id)
                conn.properties = conn_data.get("properties", {}).copy()
                graph.add_connection(conn)
                
        return graph
