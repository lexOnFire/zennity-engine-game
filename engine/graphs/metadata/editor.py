"""Metadata definitions for Editors."""
from dataclasses import dataclass

@dataclass
class EditorDefinition:
    id: str
    name_key: str
    icon: str = ""
    
    @property
    def name(self): return self.name_key
