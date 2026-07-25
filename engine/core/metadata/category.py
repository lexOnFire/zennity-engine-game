"""Metadata definitions for Categories."""
from dataclasses import dataclass
from engine.metadata.core import MetadataDefinition

@dataclass
class CategoryDefinition(MetadataDefinition):
    name_key: str = ""
    order: int = 0
    
    def __post_init__(self):
        if not self.title_key and self.name_key:
            self.title_key = self.name_key
            
    @property
    def name(self): return self.title_key
