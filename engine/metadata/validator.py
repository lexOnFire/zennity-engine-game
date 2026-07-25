"""Metadata Validation Service."""
from engine.core.services import IService
from engine.core.lifecycle import ServiceScope
from typing import List

class MetadataValidator(IService):
    """
    Validates metadata definitions to ensure consistency.
    """
    def __init__(self):
        super().__init__()
        self.scope = ServiceScope.ENGINE
        
    def initialize(self) -> None:
        pass
        
    def shutdown(self) -> None:
        pass
        
    def validate_all(self, manager) -> List[str]:
        """Runs checks across all registered definitions in the given manager."""
        errors = []
        
        # 1. Check for missing titles or descriptions (warnings)
        # 2. Check for duplicate IDs (handled at register time, but could be logged)
        # 3. Check broken refs
        
        if hasattr(manager, '_duplicate_logs'):
            errors.extend(manager._duplicate_logs)
            
        for def_type, defs_dict in manager._definitions.items():
            for def_id, definition in defs_dict.items():
                if not definition.title_key:
                    errors.append(f"Warning: {def_type.__name__} '{def_id}' is missing a title_key.")
                    
                # Check Namespace (must have at least one dot)
                if "." not in def_id and def_type.__name__ != "PluginDefinition":
                    errors.append(f"Namespace Warning: {def_type.__name__} '{def_id}' has no namespace (e.g. 'core.{def_id}').")
                    
                # Check Category
                if hasattr(definition, 'category_key') and not definition.category_key:
                    if def_type.__name__ in ("NodeDefinition", "ComponentDefinition", "AssetTypeDefinition"):
                        errors.append(f"Category Warning: {def_type.__name__} '{def_id}' is missing a category_key.")
                    
                # Check Connection broken refs if applicable
                if def_type.__name__ == "ConnectionDefinition":
                    # connection: source_node -> target_node
                    from engine.core.metadata import NodeDefinition
                    src = getattr(definition, 'source_node', None)
                    if src and not manager.get(NodeDefinition, src):
                        errors.append(f"Broken Ref: Connection '{def_id}' references unknown source node '{src}'.")
                        
                    tgt = getattr(definition, 'target_node', None)
                    if tgt and not manager.get(NodeDefinition, tgt):
                        errors.append(f"Broken Ref: Connection '{def_id}' references unknown target node '{tgt}'.")
                        
        return errors
