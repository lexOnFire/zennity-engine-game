from dataclasses import dataclass, field

@dataclass
class MetadataDefinition:
    """
    Base class for all metadata definitions in the engine.
    Standardizes identity, localization and UI categorization.
    """
    id: str
    title_key: str = ""
    description_key: str = ""
    icon: str = ""
    category_key: str = ""
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"
    namespace: str = "core"
