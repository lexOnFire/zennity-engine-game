"""Localization Manager for Zennity Engine."""
import json
from pathlib import Path
from typing import Dict, Optional

class LocalizationManager:
    """Singleton that manages loaded translations, languages, and fallbacks."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.current_locale: str = "en-US"
        self.fallback_locale: str = "en-US"
        self.base_locales_dir: Path = Path.cwd() / "locales"
        self.translations: Dict[str, str] = {}
        self.fallback_translations: Dict[str, str] = {}
        self._plugin_locales_dirs: list[Path] = []
        
    def add_locales_directory(self, path: Path):
        """Allows plugins to register their own locales folder."""
        if path not in self._plugin_locales_dirs:
            self._plugin_locales_dirs.append(path)
            self.reload()

    def set_locale(self, locale: str):
        self.current_locale = locale
        self.reload()
        
    def reload(self):
        """Hot reloads all JSON dictionaries for the current and fallback locales."""
        self.translations.clear()
        self.fallback_translations.clear()
        
        # Load fallbacks first
        self._load_into(self.fallback_locale, self.fallback_translations)
        # Load current locale
        self._load_into(self.current_locale, self.translations)
        
    def _load_into(self, locale: str, target_dict: Dict[str, str]):
        # Base engine locales
        self._load_from_dir(self.base_locales_dir / locale, target_dict)
        # Plugin locales
        for plugin_dir in self._plugin_locales_dirs:
            self._load_from_dir(plugin_dir / locale, target_dict)
            
    def _load_from_dir(self, directory: Path, target_dict: Dict[str, str]):
        if not directory.exists() or not directory.is_dir():
            return
            
        for file in directory.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        target_dict.update(data)
            except Exception as e:
                print(f"Failed to load translations from {file}: {e}")

    def translate(self, key: str, **kwargs) -> str:
        """Returns the localized string, formatting it with kwargs if provided."""
        text = self.translations.get(key, self.fallback_translations.get(key, key))
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

def tr(key: str, **kwargs) -> str:
    """Global alias for LocalizationManager().translate()"""
    return LocalizationManager().translate(key, **kwargs)
