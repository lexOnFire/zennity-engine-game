"""Plugin Manifest."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class PluginManifest:
    id: str
    version: str
    locales: str = ""
    graphs: str = ""
    assets: str = ""
    components: str = ""
    dependencies: List[str] = field(default_factory=list)
