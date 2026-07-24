"""Graph Node base architecture."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping

from engine.graphs.core.pin import GraphPin


@dataclass
class NodeMetadata:
    """Metadata para renderização visual e organização."""
    name: str = "Node"
    description: str = ""
    category: str = "Geral"
    icon: str = "default_node"
    color: str = "#444444"
    version: str = "1.0.0"
    author: str = "Zennity"
    docs_url: str = ""
    tags: list[str] = field(default_factory=list)


class GraphNode:
    """Classe base agnóstica para qualquer nó do Graph Framework."""
    
    metadata = NodeMetadata()
    
    def __init__(self, node_id: str | None = None) -> None:
        self.id = node_id or str(uuid.uuid4())
        self.position: tuple[float, float] = (0.0, 0.0)
        self.inputs: list[GraphPin] = []
        self.outputs: list[GraphPin] = []
        self.properties: dict[str, Any] = {}
        self.error_message: str | None = None
        self.warning_message: str | None = None
        self._is_breakpoint = False
        
        self.setup_pins()

    def setup_pins(self) -> None:
        """Subclasses devem sobrescrever para declarar seus pinos."""
        pass
        
    def add_input(self, pin: GraphPin) -> None:
        pin.node = self
        pin.is_input = True
        self.inputs.append(pin)
        
    def add_output(self, pin: GraphPin) -> None:
        pin.node = self
        pin.is_input = False
        self.outputs.append(pin)
        
    def get_input(self, name: str) -> GraphPin | None:
        for p in self.inputs:
            if p.name == name:
                return p
        return None
        
    def get_output(self, name: str) -> GraphPin | None:
        for p in self.outputs:
            if p.name == name:
                return p
        return None

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "position": {"x": self.position[0], "y": self.position[1]},
            "properties": self.properties.copy(),
            "is_breakpoint": self._is_breakpoint,
        }

    def deserialize(self, data: Mapping[str, Any]) -> None:
        pos = data.get("position", {"x": 0.0, "y": 0.0})
        self.position = (float(pos.get("x", 0.0)), float(pos.get("y", 0.0)))
        self.properties = data.get("properties", {}).copy()
        self._is_breakpoint = data.get("is_breakpoint", False)
