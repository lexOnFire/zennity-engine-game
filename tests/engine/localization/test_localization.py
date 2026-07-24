"""Unit Tests for Localization Manager."""
import pytest
from engine.localization import LocalizationManager, tr, LocalizationChangedEvent
from engine.event_bus import EventBus

def test_cache_independence():
    manager = LocalizationManager()
    manager._caches.clear()
    
    manager.set_locale("en-US")
    manager._ensure_cache("en-US")
    manager._caches["en-US"]["test.key"] = "Hello"
    
    manager.set_locale("pt-BR")
    manager._ensure_cache("pt-BR")
    manager._caches["pt-BR"]["test.key"] = "Ola"
    
    manager.set_locale("en-US")
    assert manager.translate("test.key") == "Hello"
    
def test_typed_events():
    manager = LocalizationManager()
    event_payload = None
    
    def on_loc_change(payload):
        nonlocal event_payload
        event_payload = payload
        
    EventBus.subscribe("LocalizationChanged", on_loc_change)
    manager.set_locale("es-ES")
    
    assert event_payload is not None
    assert isinstance(event_payload, LocalizationChangedEvent)
    assert event_payload.locale == "es-ES"
