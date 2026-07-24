"""Metadata definitions for Graph Nodes."""
from dataclasses import dataclass, field
from typing import Callable, Any
from .pin import PinDefinition

@dataclass
class NodeDefinition:
    id: str
    name: str
    category: str
    description: str = ""
    color: str = "#808080"
    icon: str = ""
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "Zennity"
    
    inputs: list[PinDefinition] = field(default_factory=list)
    outputs: list[PinDefinition] = field(default_factory=list)
    
    examples: str = ""
    best_practices: str = ""
    common_errors: str = ""
    
    # Factory for the runtime instance (if compiled)
    runtime_class: Callable[..., Any] | None = None
