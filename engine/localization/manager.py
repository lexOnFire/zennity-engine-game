"""Localization Manager for Zennity Engine."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
# Using Zennity's internal EventBus
from engine.event_bus import EventBus

logger = logging.getLogger(__name__)

class LocalizationManager:
    """Singleton for robust module-based localization."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.current_locale: str = "en-US"
        self.base_locales_dir: Path = Path.cwd() / "locales"
        self._plugin_locales_dirs: List[Path] = []
        
        # Flat cache for O(1) resolution
        self._cache: Dict[str, str] = {}
        
    def add_locales_directory(self, path: Path):
        """Allows plugins to register their own locales folder."""
        if path not in self._plugin_locales_dirs:
            self._plugin_locales_dirs.append(path)
            self.reload()

    def set_locale(self, locale: str):
        """Sets the active locale and triggers a hot reload and event dispatch."""
        if self.current_locale != locale:
            self.current_locale = locale
            self.reload()
            EventBus.publish("LocalizationChanged", {"locale": locale})
            
    def _get_fallback_chain(self, locale: str) -> List[str]:
        """Generates the fallback chain, e.g. pt-BR -> pt -> en-US."""
        chain = [locale]
        if "-" in locale:
            base = locale.split("-")[0]
            if base != locale:
                chain.append(base)
        if "en-US" not in chain:
            chain.append("en-US")
        # Reverse to load from least specific to most specific (so specific overrides general)
        chain.reverse()
        return chain
        
    def reload(self):
        """Hot reloads all JSON dictionaries into the flat cache."""
        self._cache.clear()
        
        chain = self._get_fallback_chain(self.current_locale)
        
        for loc in chain:
            # 1. Load base engine locales
            self._load_from_dir(self.base_locales_dir / loc)
            # 2. Load plugin locales (plugins can override base strings if needed)
            for plugin_dir in self._plugin_locales_dirs:
                self._load_from_dir(plugin_dir / loc)
                
    def _load_from_dir(self, directory: Path):
        """Loads all .json files in the directory and merges them into the flat cache."""
        if not directory.exists() or not directory.is_dir():
            return
            
        for file in directory.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Merge flat
                        self._cache.update(data)
            except Exception as e:
                logger.error(f"Failed to load translations from {file}: {e}")

    def translate(self, key: str, **kwargs) -> str:
        """Returns the localized string. Defaults to the key itself if not found."""
        text = self._cache.get(key, key)
        if kwargs and text != key:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

def tr(key: str, **kwargs) -> str:
    """Global alias for LocalizationManager().translate()"""
    return LocalizationManager().translate(key, **kwargs)
