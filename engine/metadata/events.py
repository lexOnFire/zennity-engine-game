from dataclasses import dataclass
from typing import Type
from engine.metadata.core import MetadataDefinition

@dataclass
class MetadataRegisteredEvent:
    def_type: Type[MetadataDefinition]
    definition: MetadataDefinition

@dataclass
class MetadataRemovedEvent:
    def_type: Type[MetadataDefinition]
    def_id: str

@dataclass
class MetadataReloadedEvent:
    pass
