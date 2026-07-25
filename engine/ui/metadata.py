"""Definições de Metadados e Widgets da Plataforma de UI da Zennity Engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from engine.metadata.core import MetadataDefinition


@dataclass
class WidgetDefinition(MetadataDefinition):
    """Metadados de um elemento de interface do usuário."""

    id: str = ""
    widget_type: str = "Control"
    category: str = "UI"
    default_width: float = 100.0
    default_height: float = 40.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UILayoutDefinition(MetadataDefinition):
    """Metadados de um leiaute de interface (.zui)."""

    id: str = ""
    name: str = "NewLayout"
    root_widgets: List[dict] = field(default_factory=list)
