"""Metadata definitions for Graph Types."""
from dataclasses import dataclass
from engine.metadata.core import MetadataDefinition

@dataclass
class GraphDefinition(MetadataDefinition):
    # id, description_key, category_key, icon, tags are inherited
    name_key: str = ""
    color: str = "#444444"
    extension: str = ".zgraph"
    can_be_nested: bool = True
    
    def __post_init__(self):
        if self.name_key and not self.title_key:
            self.title_key = self.name_key
        if self.title_key and not self.name_key:
            self.name_key = self.title_key
            
    @property
    def name(self): return self.name_key
    @property
    def description(self): return self.description_key
