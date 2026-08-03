"""Metadata definitions for Graph Connections."""
from dataclasses import dataclass
from engine.metadata.core import MetadataDefinition

@dataclass
class ConnectionDefinition(MetadataDefinition):
    source_node: str = ""
    source_pin: str = ""
    target_node: str = ""
    target_pin: str = ""
    
    def __post_init__(self):
        if not self.id and self.source_node and self.target_node:
            self.id = f"{self.source_node}:{self.source_pin}->{self.target_node}:{self.target_pin}"
