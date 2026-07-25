"""Localization Manager for Zennity Engine."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from engine.event_bus import EventBus
from .events import LocalizationChangedEvent

from engine.core.services import IService

logger = logging.getLogger(__name__)

_active_manager = None

class LocalizationManager(IService):
    """Singleton for robust module-based localization."""
    def __init__(self):
        super().__init__()
        global _active_manager
        _active_manager = self
        self.current_locale: str = "en-US"
        self.base_locales_dir: Path = Path.cwd() / "locales"
        self._plugin_locales_dirs: List[Path] = []
        
        # Multidimensional cache: _caches["pt-BR"]["graph.node.title"]
        self._caches: Dict[str, Dict[str, str]] = {}
        
    def initialize(self) -> None:
        pass
        
    def shutdown(self) -> None:
        pass
        
    def add_locales_directory(self, path: Path):
        if path not in self._plugin_locales_dirs:
            self._plugin_locales_dirs.append(path)
            # Invalidate caches to force reload
            self._caches.clear()
            self._ensure_cache(self.current_locale)

    def set_locale(self, locale: str):
        prev = self.current_locale
        if prev != locale:
            self.current_locale = locale
            self._ensure_cache(locale)
            EventBus.emit("LocalizationChanged", payload=LocalizationChangedEvent(locale=locale, previous_locale=prev))
            
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
        
    def _ensure_cache(self, locale: str):
        """Builds the cache for a specific locale if it doesn't exist."""
        if locale in self._caches:
            return
            
        self._caches[locale] = {}
        chain = self._get_fallback_chain(locale)
        
        for loc in chain:
            self._load_from_dir(self.base_locales_dir / loc, locale)
            for plugin_dir in self._plugin_locales_dirs:
                self._load_from_dir(plugin_dir / loc, locale)
                
    def _load_from_dir(self, directory: Path, target_locale: str):
        if not directory.exists() or not directory.is_dir():
            return
            
        for file in directory.rglob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._caches[target_locale].update(data)
            except Exception as e:
                logger.error(f"Failed to load translations from {file}: {e}")

    def _advanced_format(self, text: str, **kwargs) -> str:
        # FASE 7 STUBS: Plural, Gender, Currency, Dates
        # E.g. _format_currency(value), _format_date(date)
        return text.format(**kwargs)

    def translate(self, key: str, **kwargs) -> str:
        self._ensure_cache(self.current_locale)
        active_cache = self._caches[self.current_locale]
        
        text = active_cache.get(key, key)
        if kwargs and text != key:
            try:
                text = self._advanced_format(text, **kwargs)
            except KeyError:
                pass
        return text

def tr(key: str, default: str | None = None, **kwargs) -> str:
    global _active_manager
    if _active_manager:
        res = _active_manager.translate(key, **kwargs)
        if res == key and default is not None:
            return default
        return res
    return default if default is not None else key