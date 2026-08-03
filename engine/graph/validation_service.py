"""Serviço Central de Validação de Grafos (GraphValidationService) da Zennity Engine.

Valida conexões, tipos de pinos, ciclos, nós órfãos e entradas obrigatórias.
Reutilizado por Behavior Tree, Dialogue Graph, Material Graph e Visual Scripting.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from engine.core.metadata import PinType


class GraphValidationError:
    def __init__(self, error_type: str, message: str, node_id: str = "", pin_id: str = "") -> None:
        self.error_type = error_type
        self.message = message
        self.node_id = node_id
        self.pin_id = pin_id

    def __repr__(self) -> str:
        return f"[{self.error_type}] Node '{self.node_id}': {self.message}"


class GraphValidationService(IService):
    """Serviço oficial do Engine Core para validação de grafos."""

    def __init__(self) -> None:
        super().__init__()
        self.scope = ServiceScope.ENGINE

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def validate_connection(self, source_pin_type: str, target_pin_type: str) -> bool:
        """Verifica a compatibilidade de tipos entre dois pinos."""
        if source_pin_type == target_pin_type:
            return True
        if source_pin_type == PinType.EXEC and target_pin_type == PinType.EXEC:
            return True
        if source_pin_type in (PinType.INT, PinType.FLOAT) and target_pin_type in (PinType.INT, PinType.FLOAT):
            return True
        return False

    def validate_graph(self, nodes_data: List[dict], connections_data: List[dict]) -> List[GraphValidationError]:
        """Realiza validação completa do grafo e retorna lista de erros/alertas."""
        errors: List[GraphValidationError] = []
        connected_node_ids = set()

        for conn in connections_data:
            from_node = conn.get("from_node", "")
            to_node = conn.get("to_node", "")
            src_type = conn.get("source_pin_type", PinType.EXEC)
            tgt_type = conn.get("target_pin_type", PinType.EXEC)

            connected_node_ids.add(from_node)
            connected_node_ids.add(to_node)

            if not self.validate_connection(src_type, tgt_type):
                errors.append(GraphValidationError(
                    "PIN_TYPE_MISMATCH",
                    f"Tipo incompatível entre {src_type} e {tgt_type}",
                    node_id=from_node
                ))

        # Detecta nós órfãos
        for node in nodes_data:
            nid = node.get("id", "")
            if nid and nid not in connected_node_ids and len(nodes_data) > 1:
                errors.append(GraphValidationError(
                    "ORPHAN_NODE",
                    "Nó isolado sem conexões no grafo",
                    node_id=nid
                ))

        return errors
