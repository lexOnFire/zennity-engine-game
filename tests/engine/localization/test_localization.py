"""Unit Tests for Localization Manager."""
import pytest
from engine.localization import LocalizationManager, tr
from engine.event_bus import EventBus

def test_localization_fallback():
    manager = LocalizationManager()
    manager.set_locale("es-ES") # Assuming this doesn't exist yet, it should fallback to en-US or the raw key
    
    # If the key doesn't exist anywhere, it returns the key
    assert tr("unknown.key") == "unknown.key"

def test_localization_formatting():
    manager = LocalizationManager()
    manager._cache["test.fmt"] = "Hello {name}"
    assert manager.translate("test.fmt", name="Zennity") == "Hello Zennity"
    
def test_event_dispatch():
    manager = LocalizationManager()
    event_fired = False
    
    def on_loc_change(payload):
        nonlocal event_fired
        event_fired = True
        assert payload["locale"] == "fr-FR"
        
    EventBus.subscribe("LocalizationChanged", on_loc_change)
    manager.set_locale("fr-FR")
    assert event_fired
