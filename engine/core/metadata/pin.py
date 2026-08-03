"""Metadata definitions for Graph Pins."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class PinType(str, Enum):
    EXEC = "exec"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    VECTOR2 = "vector2"
    VECTOR3 = "vector3"
    COLOR = "color"
    OBJECT = "object"

from engine.metadata.core import MetadataDefinition

@dataclass
class PinDefinition(MetadataDefinition):
    pin_type: str | PinType = PinType.EXEC
    label_key: str = ""
    default_value: Any = None
    is_list: bool = False
    hide_label: bool = False
    
    def __post_init__(self):
        if isinstance(self.pin_type, PinType):
            self.pin_type = self.pin_type.value
        if not self.label_key:
            self.label_key = f"pin.{self.id}.label"
            
    # Backwards compatibility
    @property
    def label(self): return self.label_key
