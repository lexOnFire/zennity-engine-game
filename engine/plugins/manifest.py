"""Plugin Manifest."""
from dataclasses import dataclass

@dataclass
class PluginManifest:
    id: str
    version: str
    locales: str = ""  # Relative path to locales directory within the plugin
