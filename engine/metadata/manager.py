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
        # Índices otimizados
        self._idx_by_category: Dict[str, set] = {}
        self._idx_by_tag: Dict[str, set] = {}
        self._idx_by_version: Dict[str, set] = {}
        
    def initialize(self) -> None:
        pass
        
    def shutdown(self) -> None:
        self.reload()
        
    def _add_to_indices(self, definition: MetadataDefinition):
        ref = (type(definition), definition.id)
        # Index category
        cat = getattr(definition, "category_key", "")
        if cat:
            self._idx_by_category.setdefault(cat, set()).add(ref)
        # Index tags
        for tag in getattr(definition, "tags", []):
            self._idx_by_tag.setdefault(tag, set()).add(ref)
        # Index version
        ver = getattr(definition, "version", "")
        if ver:
            self._idx_by_version.setdefault(ver, set()).add(ref)
            
    def _remove_from_indices(self, definition: MetadataDefinition):
        ref = (type(definition), definition.id)
        cat = getattr(definition, "category_key", "")
        if cat and ref in self._idx_by_category.get(cat, set()):
            self._idx_by_category[cat].remove(ref)
            
        for tag in getattr(definition, "tags", []):
            if tag in self._idx_by_tag and ref in self._idx_by_tag[tag]:
                self._idx_by_tag[tag].remove(ref)
                
        ver = getattr(definition, "version", "")
        if ver and ref in self._idx_by_version.get(ver, set()):
            self._idx_by_version[ver].remove(ref)
        
    def register(self, definition: MetadataDefinition) -> None:
        """Registers a metadata definition."""
        def_type = type(definition)
        if def_type not in self._definitions:
            self._definitions[def_type] = {}
            
        if definition.id in self._definitions[def_type]:
            # Remove old definition from indices if overwriting
            self._remove_from_indices(self._definitions[def_type][definition.id])
            if not hasattr(self, '_duplicate_logs'):
                self._duplicate_logs = []
            self._duplicate_logs.append(f"Collision detected: {def_type.__name__} with ID '{definition.id}' was overwritten.")
            
        self._definitions[def_type][definition.id] = definition
        self._add_to_indices(definition)
        
        # Fire event
        from engine.core.context import EngineContext
        context = EngineContext.current()
        if context:
            from engine.event_bus import EventBus
            from engine.metadata.events import MetadataRegisteredEvent
            bus = context.services.get_optional(EventBus)
            if bus:
                bus.publish(MetadataRegisteredEvent(def_type, definition))
        
    def unregister(self, def_type: Type[T], def_id: str) -> bool:
        """Removes a metadata definition."""
        if def_type in self._definitions and def_id in self._definitions[def_type]:
            definition = self._definitions[def_type][def_id]
            self._remove_from_indices(definition)
            del self._definitions[def_type][def_id]
            
            from engine.core.context import EngineContext
            context = EngineContext.current()
            if context:
                from engine.event_bus import EventBus
                from engine.metadata.events import MetadataRemovedEvent
                bus = context.services.get_optional(EventBus)
                if bus:
                    bus.publish(MetadataRemovedEvent(def_type, def_id))
            return True
        return False
        
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
        Retrieves all definitions of a type that match the given filters, 
        using memory indices when possible for optimization.
        Example: query(NodeDefinition, category_key="Transform", tags=["math"])
        """
        if not filters:
            return self.get_all(def_type)
            
        # Try to narrow down search space using indices
        search_space = None
        
        if "category_key" in filters:
            cat_space = self._idx_by_category.get(filters["category_key"], set())
            search_space = cat_space if search_space is None else search_space.intersection(cat_space)
            
        if "version" in filters:
            ver_space = self._idx_by_version.get(filters["version"], set())
            search_space = ver_space if search_space is None else search_space.intersection(ver_space)
            
        if "tags" in filters:
            for tag in filters["tags"]:
                tag_space = self._idx_by_tag.get(tag, set())
                search_space = tag_space if search_space is None else search_space.intersection(tag_space)
                
        # If we didn't use any index, fall back to full scan
        if search_space is None:
            all_defs = self.get_all(def_type)
        else:
            # search_space contains refs (type, id)
            all_defs = []
            for ref_type, ref_id in search_space:
                if issubclass(ref_type, def_type):
                    obj = self.get(ref_type, ref_id)
                    if obj:
                        all_defs.append(obj)
            
        results = []
        for d in all_defs:
            match = True
            for k, v in filters.items():
                # Skip what we already filtered via index
                if k in ["category_key", "version", "tags"]:
                    continue
                elif not hasattr(d, k) or getattr(d, k) != v:
                    match = False
                    break
            if match:
                results.append(d) # type: ignore
                
        # Sort results deterministically by id to prevent test flakiness and ensure UI stability
        results.sort(key=lambda x: getattr(x, "id", ""))
        return results
        
    def find(self, def_type: Type[T], **filters) -> T | None:
        """Finds the first definition matching the filters."""
        results = self.query(def_type, **filters)
        return results[0] if results else None
        
    def list_ids(self, def_type: Type[T]) -> List[str]:
        """Lists all registered IDs of a specific type."""
        if def_type not in self._definitions:
            return []
        return list(self._definitions[def_type].keys())
        
    def reload(self) -> None:
        """Clears and allows providers to re-register metadata."""
        self._definitions.clear()
        self._idx_by_category.clear()
        self._idx_by_tag.clear()
        self._idx_by_version.clear()
        
        from engine.core.context import EngineContext
        context = EngineContext.current()
        if context:
            from engine.event_bus import EventBus
            from engine.metadata.events import MetadataReloadedEvent
            bus = context.services.get_optional(EventBus)
            if bus:
                bus.publish(MetadataReloadedEvent())
        
    def validate(self) -> List[str]:
        """Validates the integrity of all registered metadata."""
        from engine.core.context import EngineContext
        from engine.metadata.validator import MetadataValidator
        
        context = EngineContext.current()
        if context:
            validator = context.services.get_optional(MetadataValidator)
            if validator:
                return validator.validate_all(self)
        return ["MetadataValidator not available."]
