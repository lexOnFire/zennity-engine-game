"""Definições de Metadados da Extension Platform / Plugin Ecosystem da Zennity Engine."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from engine.metadata.core import MetadataDefinition


class ExtensionType(str, Enum):
    PLUGIN = "Plugin"
    TEMPLATE = "Template"
    ASSET_PACK = "Asset Pack"
    NODE_PACK = "Node Pack"
    THEME = "Theme"
    EXTENSION = "Extension"
    SAMPLE_PROJECT = "Sample Project"


@dataclass
class ExtensionPackageDefinition(MetadataDefinition):
    """Metadados de pacotes da Extension Platform (.zext e .zplugin)."""

    id: str = ""
    name: str = "ExtensionPackage"
    version: str = "1.0.0"
    extension_type: str = ExtensionType.PLUGIN.value
    author: str = "Zennity Ecosystem"
    description: str = "Extensão oficial da Zennity Engine"
    enabled: bool = True
    extensions: List[str] = field(default_factory=lambda: [".zext", ".zplugin"])
