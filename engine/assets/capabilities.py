"""Capacidades Transversais de Assets (AssetCapabilities) da Zennity Engine.

Garante que QUALQUER asset registrado no MetadataManager herde automaticamente:
- Pesquisabilidade (Searchable)
- Pré-visualização (Previewable)
- Grafo de Dependências (DependencyGraphParticipant)
- Exportação & Build (Exportable)
- Validação (Validatable)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from engine.metadata.core import MetadataDefinition


@dataclass
class AssetCapabilityDefinition(MetadataDefinition):
    """Definição de capacidades transversais para tipos de asset."""

    id: str = ""
    is_searchable: bool = True
    is_previewable: bool = True
    has_dependencies: bool = True
    is_exportable: bool = True
    is_validatable: bool = True
    tags: List[str] = field(default_factory=list)


class AssetCapabilitiesRegistry:
    """Registrador e inspetor central de capacidades de assets."""

    _capabilities: Dict[str, AssetCapabilityDefinition] = {}

    @classmethod
    def register(cls, asset_type_id: str, cap: AssetCapabilityDefinition) -> None:
        cls._capabilities[asset_type_id] = cap

    @classmethod
    def get(cls, asset_type_id: str) -> AssetCapabilityDefinition:
        return cls._capabilities.get(asset_type_id, AssetCapabilityDefinition(id=asset_type_id))
