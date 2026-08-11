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

    #: Phase 9.5B Stage 1 -- how this node participates in flow execution.
    #: Values come from ``engine.logic.contracts.ExecutionModel``; kept as a
    #: plain string so ``engine.core`` does not import ``engine.logic``.
    #:
    #:   "action"        an executor runs it and returns exec ports (default)
    #:   "event_source"  flow starts here; the frame loop drives it, no executor
    #:   "terminal"      flow legitimately stops here; executor returns []
    #:   "pure_data"     no exec ports; resolved by an evaluator on demand
    #:
    #: Recorded on the definition so the contract validator does not need a
    #: hardcoded exception list that drifts forever.
    execution_model: str = "action"

    #: Exec-port prefixes this node generates at runtime, e.g. ``("then_",)``
    #: for ``sequence``, which returns then_0..then_N based on a property.
    dynamic_exec_prefixes: tuple[str, ...] = ()

    #: Kept loadable for existing assets, but hidden from the palette so it
    #: cannot be used in new graphs.  Phase 9.5B Stage 1 marks nodes that have
    #: no runtime handler at all this way instead of offering a node that
    #: silently does nothing.
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
