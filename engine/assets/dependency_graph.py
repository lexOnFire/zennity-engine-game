"""Grafo de Dependências de Assets (AssetDependencyGraph) da Zennity Engine.

Mapeia e visualiza referências cruzadas entre assets, cenas, scripts e extensões.
Reutiliza o Graph Framework oficial.
"""
from __future__ import annotations
from typing import Dict, List, Set


class AssetDependencyNode:
    def __init__(self, asset_path: str, asset_type: str) -> None:
        self.asset_path = asset_path
        self.asset_type = asset_type
        self.dependencies: Set[str] = set()
        self.referenced_by: Set[str] = set()


class AssetDependencyGraph:
    """Gerenciador central do Grafo de Dependências de Assets."""

    def __init__(self) -> None:
        self._nodes: Dict[str, AssetDependencyNode] = {}

    def register_asset(self, path: str, asset_type: str) -> AssetDependencyNode:
        if path not in self._nodes:
            self._nodes[path] = AssetDependencyNode(path, asset_type)
        return self._nodes[path]

    def add_dependency(self, source_path: str, target_path: str) -> None:
        src = self._nodes.get(source_path) or self.register_asset(source_path, "generic")
        tgt = self._nodes.get(target_path) or self.register_asset(target_path, "generic")

        src.dependencies.add(target_path)
        tgt.referenced_by.add(source_path)

    def get_dependencies(self, path: str) -> List[str]:
        node = self._nodes.get(path)
        return list(node.dependencies) if node else []

    def get_references(self, path: str) -> List[str]:
        node = self._nodes.get(path)
        return list(node.referenced_by) if node else []

    def to_graph_data(self) -> dict:
        """Converte a estrutura para visualização no GenericGraphEditorWidget."""
        nodes = []
        connections = []
        for path, node in self._nodes.items():
            nodes.append({"id": path, "type": f"asset.{node.asset_type}", "inputs": {}, "outputs": {}})
            for dep in node.dependencies:
                connections.append({"from_node": path, "to_node": dep})
        return {"name": "AssetDependencyGraph", "nodes": nodes, "connections": connections}
