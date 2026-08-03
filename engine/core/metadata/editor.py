"""Metadata definitions for Editors."""
from dataclasses import dataclass, field
from engine.metadata.core import MetadataDefinition

@dataclass
class EditorDefinition(MetadataDefinition):
    name_key: str = ""
    
    def __post_init__(self):
        if not self.title_key and self.name_key:
            self.title_key = self.name_key
            
    @property
    def name(self): return self.title_key
    
@dataclass
class PropertyDefinition:
    """
    Defines a property that can be edited in the inspector.
    """
    id: str
    type_name: str # e.g. 'int', 'string', 'bool', 'vector2', 'color'
    title_key: str = ""
    default_value: object = None
    min_value: object = None
    max_value: object = None
    options: list = field(default_factory=list)
    
    def __post_init__(self):
        if not self.title_key:
            self.title_key = self.id.capitalize()

@dataclass
class InspectorDefinition(MetadataDefinition):
    """
    Defines an inspector layout for a specific component or object type.
    """
    target_type: str = ""
    properties: list[PropertyDefinition] = field(default_factory=list)
    custom_widget: type | None = None
