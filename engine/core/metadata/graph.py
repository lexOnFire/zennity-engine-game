"""Metadata definitions for Graph Types."""
from dataclasses import dataclass

@dataclass
class GraphDefinition:
    id: str
    name_key: str
    description_key: str = ""
    icon: str = ""
    color: str = "#444444"
    extension: str = ".zgraph"
    can_be_nested: bool = True
    
    @property
    def name(self): return self.name_key
    @property
    def description(self): return self.description_key
