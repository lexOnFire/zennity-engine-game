"""Unit Tests for Localization Manager."""
import pytest
from engine.localization import LocalizationManager, tr

def test_localization_fallback():
    manager = LocalizationManager()
    manager.set_locale("es-ES") # Assuming this doesn't exist yet, it should fallback to en-US or the raw key
    
    # If the key doesn't exist anywhere, it returns the key
    assert tr("unknown.key") == "unknown.key"

def test_localization_formatting():
    manager = LocalizationManager()
    manager.translations["test.fmt"] = "Hello {name}"
    assert manager.translate("test.fmt", name="Zennity") == "Hello Zennity"
