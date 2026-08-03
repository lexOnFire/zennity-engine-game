"""Sistema de Prefabs Avançado (Variantes, Overrides, Herança e Sincronização)."""
from __future__ import annotations
from typing import Dict, Any, Optional


class PrefabOverride:
    def __init__(self, property_path: str, value: Any) -> None:
        self.property_path = property_path
        self.value = value


class PrefabAsset:
    def __init__(self, name: str, parent_prefab: Optional[PrefabAsset] = None) -> None:
        self.name = name
        self.parent_prefab = parent_prefab
        self.base_properties: Dict[str, Any] = {}
        self.overrides: Dict[str, PrefabOverride] = {}

    def set_property(self, path: str, val: Any) -> None:
        if self.parent_prefab and path in self.parent_prefab.get_resolved_properties():
            self.overrides[path] = PrefabOverride(path, val)
        else:
            self.base_properties[path] = val

    def get_resolved_properties(self) -> Dict[str, Any]:
        """Herança de propriedades com aplicação de overrides."""
        props = {}
        if self.parent_prefab:
            props.update(self.parent_prefab.get_resolved_properties())
        props.update(self.base_properties)
        for path, override in self.overrides.items():
            props[path] = override.value
        return props
