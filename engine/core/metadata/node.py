"""Metadata definitions for Graph Nodes."""
from dataclasses import dataclass, field
from typing import Callable, Any
from .pin import PinDefinition

@dataclass
class NodeDefinition:
    id: str
    name_key: str  # Migration from 'name'
    category_key: str  # Migration from 'category'
    description_key: str = ""  # Migration from 'description'
    color: str = "#808080"
    icon: str = ""
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "Zennity"
    
    inputs: list[PinDefinition] = field(default_factory=list)
    outputs: list[PinDefinition] = field(default_factory=list)
    
    examples_key: str = ""
    best_practices_key: str = ""
    common_errors_key: str = ""
    
    runtime_class: Callable[..., Any] | None = None
    
    # Backwards compatibility properties (deprecated)
    @property
    def name(self): return self.name_key
    @property
    def category(self): return self.category_key
    @property
    def description(self): return self.description_key
