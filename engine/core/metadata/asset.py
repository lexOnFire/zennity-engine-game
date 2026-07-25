"""Metadata definitions for Assets."""
from dataclasses import dataclass, field
from engine.metadata.core import MetadataDefinition
from typing import List

@dataclass
class AssetTypeDefinition(MetadataDefinition):
    """
    Defines an asset type (e.g., Image, Scene) and its associated file extensions.
    """
    extensions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.title_key and self.id:
            self.title_key = self.id.capitalize()

@dataclass
class ImporterDefinition(MetadataDefinition):
    """
    Defines an asset importer.
    """
    extensions: List[str] = field(default_factory=list)
    importer_class: type | None = None
    
@dataclass
class ExporterDefinition(MetadataDefinition):
    """
    Defines an asset exporter.
    """
    extensions: List[str] = field(default_factory=list)
    exporter_class: type | None = None
