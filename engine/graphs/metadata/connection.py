"""Metadata definitions for Graph Connections."""
from dataclasses import dataclass

@dataclass
class ConnectionDefinition:
    source_node: str
    source_pin: str
    target_node: str
    target_pin: str
    label_key: str = ""
