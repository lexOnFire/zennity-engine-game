"""Metadata definitions for Graph Nodes."""
from dataclasses import dataclass, field
from typing import Callable, Any
from .pin import PinDefinition
from engine.metadata.core import MetadataDefinition

@dataclass
class NodeDefinition(MetadataDefinition):
    # id, description_key, category_key, icon, tags are inherited
    name_key: str = "" # Backwards compatibility alias for title_key
    color: str = "#808080"
    keywords: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    author: str = "Zennity"
    
    inputs: list[PinDefinition] = field(default_factory=list)
    outputs: list[PinDefinition] = field(default_factory=list)
    
    examples_key: str = ""
    best_practices_key: str = ""
    common_errors_key: str = ""
    
    runtime_class: Callable[..., Any] | None = None
    executor: Callable[..., Any] | None = None
    evaluator: Callable[..., Any] | None = None

    # PHASE 9 recovery item 1. Stage 1's declarative modules -- math_nodes,
    # logic_nodes, scene_nodes -- declare these, and without the fields they
    # fail to import with a TypeError, taking three whole domains out of the
    # palette. Accepted and stored here so those modules load; what the
    # catalogue *does* with the values is deliberately not decided in this item
    # (execution_model unification is its own recovery item), so nothing reads
    # them yet.
    execution_model: str | None = None
    dynamic_exec_prefixes: tuple[str, ...] = ()
    deprecated: bool = False


    def __post_init__(self):
        if self.name_key and not self.title_key:
            self.title_key = self.name_key
        if self.title_key and not self.name_key:
            self.name_key = self.title_key
            
    # Backwards compatibility properties (deprecated)
    @property
    def name(self): return self.name_key
    @property
    def category(self): return self.category_key
    @property
    def description(self): return self.description_key
