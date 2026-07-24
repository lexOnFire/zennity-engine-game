"""Metadata definitions for Categories."""
from dataclasses import dataclass

@dataclass
class CategoryDefinition:
    id: str
    name: str
    icon: str = ""
    color: str = ""
    order: int = 0
