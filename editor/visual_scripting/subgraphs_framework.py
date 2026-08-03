"""Subgraphs & Macro Nodes Framework — Sprint 14 (Visual Scripting 2.0).

Recursos de produtividade avançados:
  - Subgraphs: Nó composto que esconde uma sub-rede de nós em um único nó legível.
  - Macro Nodes: Receitas de macros reutilizáveis que podem ser expandidas ou recolhidas (Collapse / Expand).
  - Command Palette: Menu de comandos rápidos de busca (Ctrl+K).
"""
from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4


class SubgraphNodeManager:
    """Gerencia a criação e expansão de Subgrafos e Macros no Visual Scripting 2.0."""

    def __init__(self) -> None:
        self.registered_macros: dict[str, dict[str, Any]] = {}

    def create_subgraph_node(self, title: str, inner_nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """Empacota uma seleção de nós internos em um Subgrafo único."""
        subgraph_id = uuid4().hex
        macro_def = {
            "id": subgraph_id,
            "title": title,
            "category": "Subgrafos",
            "type": "call_subgraph",
            "inner_nodes": inner_nodes,
            "inputs": [("in", "flow"), ("params", "any")],
            "outputs": [("out", "flow"), ("result", "any")],
            "collapsed": True,
        }
        self.registered_macros[subgraph_id] = macro_def
        return macro_def

    def expand_subgraph(self, subgraph_id: str) -> list[dict[str, Any]]:
        """Expande os nós internos de um Subgrafo (Expand Nodes)."""
        macro = self.registered_macros.get(subgraph_id)
        if macro:
            return macro.get("inner_nodes", [])
        return []
