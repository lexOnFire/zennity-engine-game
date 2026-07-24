import pytest
from engine.core.bootstrap import EngineBootstrap
from engine.core.context import EngineContext
from engine.localization.manager import LocalizationManager
from engine.graphs.plugins.manager import PluginManager

def test_bootstrap_discovers_and_initializes_providers():
    context = EngineBootstrap.boot()
    
    # Validation 1: Context is created properly
    assert isinstance(context, EngineContext)
    
    # Validation 2: Localization Provider was discovered and registered LocalizationManager
    loc_manager = context.services.get(LocalizationManager)
    assert isinstance(loc_manager, LocalizationManager)
    assert loc_manager.base_locales_dir == context.locales_dir
    
    # Validation 3: Plugin Provider was discovered and registered PluginManager
    plugin_manager = context.services.get(PluginManager)
    assert isinstance(plugin_manager, PluginManager)

def test_bootstrap_initializes_services(monkeypatch):
    called = False
    def mock_init_all():
        nonlocal called
        called = True
        
    monkeypatch.setattr('engine.core.services.EngineServices.initialize_all', mock_init_all)
    
    context = EngineBootstrap.boot()
    
    # Validation 4: initialize_all was called
    assert called is True
