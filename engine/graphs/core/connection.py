"""Graph Connection base architecture."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from engine.graphs.core.node import GraphNode
    from engine.graphs.core.pin import GraphPin


class GraphConnection:
    """Representa a ligação entre dois pinos de dois nós distintos."""
    
    def __init__(self, from_node: GraphNode, from_pin: GraphPin, to_node: GraphNode, to_pin: GraphPin) -> None:
        self.id = str(uuid.uuid4())
        self.from_node = from_node
        self.from_pin = from_pin
        self.to_node = to_node
        self.to_pin = to_pin
        
        # Pode armazenar propriedades da conexão, como delay ou tipo de conversão visual.
        self.properties: dict[str, Any] = {}

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from_node": self.from_node.id,
            "from_pin": self.from_pin.name,
            "to_node": self.to_node.id,
            "to_pin": self.to_pin.name,
            "properties": self.properties.copy(),
        }
