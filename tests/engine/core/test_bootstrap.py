import pytest
from engine.core.bootstrap import EngineBootstrap
from engine.core.context import EngineContext
from engine.core.provider import EngineProvider
from engine.localization.manager import LocalizationManager
from engine.graphs.plugins.manager import PluginManager
from engine.core.lifecycle import BootProfile

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
    
    assert isinstance(context, EngineContext)
    
    assert "total_boot_time" in context.diagnostics
    assert "provider_boot_times" in context.diagnostics
    assert "CoreProvider" in context.diagnostics["provider_boot_times"]
    
    loc_manager = context.services.get(LocalizationManager)
    assert isinstance(loc_manager, LocalizationManager)
    assert loc_manager.base_locales_dir == context.locales_dir
    
    plugin_manager = context.services.get(PluginManager)
    assert isinstance(plugin_manager, PluginManager)

def test_bootstrap_initializes_services(monkeypatch):
    called = False
    def mock_init_all(self, context=None):
        nonlocal called
        called = True
        
    monkeypatch.setattr('engine.core.services.EngineServices.initialize_all', mock_init_all)
    
    context = EngineBootstrap.boot()
    
    assert called is True

# --- Boot Profiles Testing ---

class RuntimeOnlyProvider(EngineProvider):
    profiles = [BootProfile.RUNTIME]
    def register_services(self, context):
        context.diagnostics["runtime_loaded"] = True

class EditorOnlyProvider(EngineProvider):
    profiles = [BootProfile.EDITOR]
    def register_services(self, context):
        context.diagnostics["editor_loaded"] = True

class SharedProvider(EngineProvider):
    profiles = [BootProfile.RUNTIME, BootProfile.EDITOR]
    def register_services(self, context):
        context.diagnostics["shared_loaded"] = True

def test_bootstrap_filters_by_profile(monkeypatch):
    def mock_discover():
        return [RuntimeOnlyProvider, EditorOnlyProvider, SharedProvider]
    
    monkeypatch.setattr('engine.core.bootstrap.EngineBootstrap._discover_providers', mock_discover)
    
    # Test EDITOR profile
    ctx_editor = EngineBootstrap.boot(profile=BootProfile.EDITOR)
    assert ctx_editor.diagnostics.get("editor_loaded") is True
    assert ctx_editor.diagnostics.get("shared_loaded") is True
    assert ctx_editor.diagnostics.get("runtime_loaded") is None
    
    # Test RUNTIME profile
    ctx_runtime = EngineBootstrap.boot(profile=BootProfile.RUNTIME)
    assert ctx_runtime.diagnostics.get("editor_loaded") is None
    assert ctx_runtime.diagnostics.get("shared_loaded") is True
    assert ctx_runtime.diagnostics.get("runtime_loaded") is True
    
    # Test HEADLESS profile
    ctx_headless = EngineBootstrap.boot(profile=BootProfile.HEADLESS)
    assert ctx_headless.diagnostics.get("editor_loaded") is None
    assert ctx_headless.diagnostics.get("shared_loaded") is None
    assert ctx_headless.diagnostics.get("runtime_loaded") is None
