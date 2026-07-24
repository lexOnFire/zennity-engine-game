"""Metadata definitions for Graph Types."""
from dataclasses import dataclass, field

@dataclass
class GraphDefinition:
    id: str
    name: str
    description: str = ""
    icon: str = ""
    color: str = "#444444"
    extension: str = ".zgraph"
    # Determines if this graph can be nested as a SubGraph
    can_be_nested: bool = True
