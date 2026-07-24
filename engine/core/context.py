"""Engine Context.

Holds the core state and services for the Zennity Engine during runtime or editor sessions.
"""
from typing import Dict, Any, Optional
from pathlib import Path
from engine.core.services import EngineServices


class EngineContext:
    """The central context passed to all EngineProviders during bootstrap."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config: Dict[str, Any] = config or {}
        
        # Core Services Locator is accessible from the context
        self.services = EngineServices
        
        # Fundamental engine state
        self.version: str = "2.0.0"
        self.platform: str = "Unknown"  # OS Platform, will be populated
        
        # Standard directories
        self.root_dir: Path = Path.cwd()
        self.assets_dir: Path = self.root_dir / "Assets"
        self.plugins_dir: Path = self.root_dir / "plugins"
        self.locales_dir: Path = self.root_dir / "locales"
        
        # User settings
        self.settings: Dict[str, Any] = {}
        
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
