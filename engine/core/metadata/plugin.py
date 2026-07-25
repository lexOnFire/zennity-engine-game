from dataclasses import dataclass, field
from engine.metadata.core import MetadataDefinition

@dataclass
class PluginDefinition(MetadataDefinition):
    """Metadata definition for a Plugin or Extension."""
    version: str = "1.0.0"
    author: str = "Unknown"
    module_name: str = ""
    entry_point: str = ""
    locales_dir: str = ""
    dependencies: list[str] = field(default_factory=list)
