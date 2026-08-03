"""Graph Pin (Port) base architecture."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from engine.graphs.core.node import GraphNode


class GraphPin:
    """Representa uma porta de entrada ou saída em um nó genérico."""
    
    def __init__(
        self, 
        name: str, 
        pin_type: str, 
        display_name: str | None = None,
        default_value: Any = None,
        max_connections: int = 1, # -1 para infinito
    ) -> None:
        self.name = name
        self.display_name = display_name or name
        self.pin_type = pin_type
        self.default_value = default_value
        self.max_connections = max_connections
        self.node: GraphNode | None = None
        self.is_input: bool = True
        
    def can_connect_to(self, other_pin: GraphPin) -> bool:
        """Validação básica de conexão de pinos. Pode ser herdada e expandida."""
        if self.node is other_pin.node:
            return False  # Evitar self-connection no mesmo nó
        if self.is_input == other_pin.is_input:
            return False  # Entrada não conecta em Entrada
        return True
