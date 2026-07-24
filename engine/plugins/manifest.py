"""Plugin Manifest."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class PluginManifest:
    id: str
    version: str
    
    # Automatic Discovery (Directories)
    locales: str = ""
    graphs: str = ""
    assets: str = ""
    documentation: str = ""
    templates: str = ""
    components: str = ""
    
    # FQDN Lists for injection
    services: List[str] = field(default_factory=list)
    nodes: List[str] = field(default_factory=list)
    pin_types: List[str] = field(default_factory=list)
    inspectors: List[str] = field(default_factory=list)
    serializers: List[str] = field(default_factory=list)
    compilers: List[str] = field(default_factory=list)
    runtimes: List[str] = field(default_factory=list)
    
    dependencies: List[str] = field(default_factory=list)
