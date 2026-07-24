import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class Translator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._locales_path = Path(__file__).parent / "locales"
        self._current_lang = "pt"
        self._translations = {}
        
        self.set_language("pt")
        self._initialized = True

    def set_language(self, lang: str) -> None:
        """Define o idioma atual e carrega o arquivo JSON correspondente."""
        self._current_lang = lang
        self._translations.clear()
        
        locale_file = self._locales_path / f"{lang}.json"
        
        if locale_file.exists():
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self._translations = json.load(f)
                logger.info(f"Idioma carregado: {lang}")
            except Exception as e:
                logger.error(f"Falha ao carregar idioma {lang}: {e}")
        else:
            logger.warning(f"Arquivo de idioma não encontrado: {locale_file}")

    def translate(self, key: str, default: str | None = None) -> str:
        """
        Retorna a string traduzida para a chave especificada.
        Se não existir, retorna o default (se fornecido) ou a própria key.
        """
        if not key:
            return ""
            
        parts = key.split(".")
        current = self._translations
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default if default is not None else key
                
        if isinstance(current, str):
            return current
            
        return default if default is not None else key


# Helper global para uso rápido, ex: tr("editor.file")
def tr(key: str, default: str | None = None) -> str:
    return Translator().translate(key, default)
