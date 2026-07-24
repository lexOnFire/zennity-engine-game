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
    # Custom types handled via string comparison if not in enum

@dataclass
class PinDefinition:
    id: str
    pin_type: str | PinType
    label: str = ""
    description: str = ""
    default_value: Any = None
    is_list: bool = False
    hide_label: bool = False
    
    def __post_init__(self):
        if isinstance(self.pin_type, PinType):
            self.pin_type = self.pin_type.value
        if not self.label:
            self.label = self.id.capitalize()
