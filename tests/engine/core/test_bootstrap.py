import pytest
from engine.core.bootstrap import EngineBootstrap
from engine.core.context import EngineContext
from engine.core.provider import EngineProvider
from engine.localization.manager import LocalizationManager
from engine.graphs.plugins.manager import PluginManager

class ProviderA(EngineProvider):
    depends_on = []
    def register_services(self, context): pass

class ProviderB(EngineProvider):
    depends_on = [ProviderA]
    def register_services(self, context): pass

class ProviderC(EngineProvider):
    depends_on = [ProviderB]
    def register_services(self, context): pass

class ProviderCycle1(EngineProvider):
    pass # depends_on assigned below

class ProviderCycle2(EngineProvider):
    depends_on = [ProviderCycle1]
    def register_services(self, context): pass

ProviderCycle1.depends_on = [ProviderCycle2]


def test_topological_sort_correct_order():
    # Misturar ordem
    providers = [ProviderC, ProviderA, ProviderB]
    sorted_provs = EngineBootstrap._topological_sort(providers)
    
    assert sorted_provs[0] == ProviderA
    assert sorted_provs[1] == ProviderB
    assert sorted_provs[2] == ProviderC

def test_topological_sort_circular_dependency():
    providers = [ProviderCycle1, ProviderCycle2]
    with pytest.raises(RuntimeError) as exc_info:
        EngineBootstrap._topological_sort(providers)
    
    assert "Circular dependency detected" in str(exc_info.value)

def test_bootstrap_discovers_and_initializes_providers():
    context = EngineBootstrap.boot()
    
    # Validation 1: Context is created properly
    assert isinstance(context, EngineContext)
    
    # Validation 2: Diagnostics exists
    assert "total_boot_time" in context.diagnostics
    assert "provider_boot_times" in context.diagnostics
    assert "CoreProvider" in context.diagnostics["provider_boot_times"]
    
    # Validation 3: Localization Provider was discovered and registered LocalizationManager
    loc_manager = context.services.get(LocalizationManager)
    assert isinstance(loc_manager, LocalizationManager)
    assert loc_manager.base_locales_dir == context.locales_dir
    
    # Validation 4: Plugin Provider was discovered and registered PluginManager
    plugin_manager = context.services.get(PluginManager)
    assert isinstance(plugin_manager, PluginManager)

def test_bootstrap_initializes_services(monkeypatch):
    called = False
    def mock_init_all(self, context=None):
        nonlocal called
        called = True
        
    monkeypatch.setattr('engine.core.services.EngineServices.initialize_all', mock_init_all)
    
    context = EngineBootstrap.boot()
    
    # Validation 5: initialize_all was called
    assert called is True
