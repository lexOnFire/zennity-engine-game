"""Metadata Manager Service."""
from typing import Dict, Type, TypeVar, Any, List
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from engine.metadata.core import MetadataDefinition

T = TypeVar('T', bound=MetadataDefinition)

class MetadataManager(IService):
    """
    Central service for registering and querying all metadata definitions
    in the Zennity Engine.
    """
    def __init__(self):
        super().__init__()
        self.scope = ServiceScope.ENGINE
        self._definitions: Dict[Type[MetadataDefinition], Dict[str, MetadataDefinition]] = {}
        
    def initialize(self) -> None:
        pass
        
    def shutdown(self) -> None:
        self._definitions.clear()
        
    def register(self, definition: MetadataDefinition) -> None:
        """Registers a metadata definition."""
        def_type = type(definition)
        if def_type not in self._definitions:
            self._definitions[def_type] = {}
            
        if definition.id in self._definitions[def_type]:
            # Overwriting could be warned, but we allow it for hot-reloading
            pass
            
        self._definitions[def_type][definition.id] = definition
        
    def get(self, def_type: Type[T], def_id: str) -> T | None:
        """Retrieves a specific definition by ID."""
        if def_type not in self._definitions:
            return None
        return self._definitions[def_type].get(def_id)  # type: ignore
        
    def get_all(self, def_type: Type[T]) -> List[T]:
        """Retrieves all registered definitions of a specific type."""
        if def_type not in self._definitions:
            return []
        return list(self._definitions[def_type].values()) # type: ignore
        
    def query(self, def_type: Type[T], **filters) -> List[T]:
        """
        Retrieves all definitions of a type that match the given filters.
        Example: query(NodeDefinition, category_key="Transform")
        """
        all_defs = self.get_all(def_type)
        results = []
        for d in all_defs:
            match = True
            for k, v in filters.items():
                if not hasattr(d, k) or getattr(d, k) != v:
                    match = False
                    break
            if match:
                results.append(d)
        return results
