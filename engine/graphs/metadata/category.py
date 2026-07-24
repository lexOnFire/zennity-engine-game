"""Metadata definitions for Categories."""
from dataclasses import dataclass

@dataclass
class CategoryDefinition:
    id: str
    name_key: str
    icon: str = ""
    color: str = ""
    order: int = 0
    
    @property
    def name(self): return self.name_key
