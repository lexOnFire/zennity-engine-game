"""Localization Manager for Zennity Engine."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
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
        self._cache: Dict[str, str] = {}
        
    def add_locales_directory(self, path: Path):
        if path not in self._plugin_locales_dirs:
            self._plugin_locales_dirs.append(path)
            self.reload()

    def set_locale(self, locale: str):
        if self.current_locale != locale:
            self.current_locale = locale
            self.reload()
            EventBus.publish("LocalizationChanged", {"locale": locale})
            
    def _get_fallback_chain(self, locale: str) -> List[str]:
        chain = [locale]
        if "-" in locale:
            base = locale.split("-")[0]
            if base != locale:
                chain.append(base)
        if "en-US" not in chain:
            chain.append("en-US")
        chain.reverse()
        return chain
        
    def reload(self):
        self._cache.clear()
        chain = self._get_fallback_chain(self.current_locale)
        
        for loc in chain:
            self._load_from_dir(self.base_locales_dir / loc)
            for plugin_dir in self._plugin_locales_dirs:
                self._load_from_dir(plugin_dir / loc)
                
    def _load_from_dir(self, directory: Path):
        if not directory.exists() or not directory.is_dir():
            return
            
        # PHASE 5: Recursive load
        for file in directory.rglob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._cache.update(data)
            except Exception as e:
                logger.error(f"Failed to load translations from {file}: {e}")

    def _advanced_format(self, text: str, **kwargs) -> str:
        # PHASE 7 STUB: Pluralization, Gender, RTL parsing could go here
        # E.g., handling syntax like {count, plural, =1 {item} other {items}}
        # For now, we just pass down to normal format
        return text.format(**kwargs)

    def translate(self, key: str, **kwargs) -> str:
        text = self._cache.get(key, key)
        if kwargs and text != key:
            try:
                text = self._advanced_format(text, **kwargs)
            except KeyError:
                pass
        return text

def tr(key: str, **kwargs) -> str:
    return LocalizationManager().translate(key, **kwargs)
