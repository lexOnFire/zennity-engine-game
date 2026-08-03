"""Compilador de Grafos (GraphCompiler) da Zennity Engine.

Compila definições visuais de grafos (.zlogic, .zbehavior, .zdialogue, .zmat)
em instruções de execução prontas para o GraphExecutor em runtime.
"""
from __future__ import annotations
from typing import Any, Dict, List


class CompiledGraphInstruction:
    def __init__(self, node_id: str, node_type: str, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        self.node_id = node_id
        self.node_type = node_type
        self.inputs = inputs
        self.outputs = outputs


class CompiledGraph:
    def __init__(self, name: str, instructions: List[CompiledGraphInstruction], entry_node_id: str = "") -> None:
        self.name = name
        self.instructions = instructions
        self.entry_node_id = entry_node_id
        self.instructions_by_id = {inst.node_id: inst for inst in instructions}


class GraphCompiler:
    """Compilador estático de grafos da Zennity Engine."""

    @classmethod
    def compile(cls, graph_data: Dict[str, Any]) -> CompiledGraph:
        name = str(graph_data.get("name", "CompiledGraph"))
        nodes_raw = list(graph_data.get("nodes", []))
        connections_raw = list(graph_data.get("connections", []))

        instructions: List[CompiledGraphInstruction] = []
        entry_id = ""

        for ndata in nodes_raw:
            nid = str(ndata.get("id", ""))
            ntype = str(ndata.get("type", "generic"))
            inputs = dict(ndata.get("inputs", {}))
            outputs = dict(ndata.get("outputs", {}))

            if not entry_id and ("start" in ntype.lower() or "in" in ntype.lower()):
                entry_id = nid

            instructions.append(CompiledGraphInstruction(nid, ntype, inputs, outputs))

        if not entry_id and instructions:
            entry_id = instructions[0].node_id

        return CompiledGraph(name, instructions, entry_id)
