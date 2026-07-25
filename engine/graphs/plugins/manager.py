"""Plugin Manager for dynamic loading (IService)."""
import importlib
import pkgutil
from pathlib import Path
from engine.core.services import EngineServices, IService

class PluginManager(IService):
    """Discovers and initializes engine plugins."""
    
    def __init__(self):
        super().__init__()
        self.loaded_plugins = []
        
    def initialize(self, context=None) -> None:
        self.load_all_plugins(context=context)
        
    def shutdown(self) -> None:
        self.loaded_plugins.clear()
    
    def load_all_plugins(self, plugins_package="engine.plugins", context=None):
        try:
            package = importlib.import_module(plugins_package)
        except ImportError:
            return
            
        if not hasattr(package, "__path__"):
            return
            
        # Needs LocalizationManager if we register locales
        loc_manager = None
        if context:
            from engine.localization import LocalizationManager
            loc_manager = context.services.get_optional(LocalizationManager)
            
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                full_module_name = f"{plugins_package}.{module_name}"
                try:
                    plugin_module = importlib.import_module(full_module_name)
                    plugin_path = Path(plugin_module.__file__).parent
                    
                    plugin_class_name = module_name.capitalize() + "Plugin"
                    if hasattr(plugin_module, plugin_class_name):
                        plugin_cls = getattr(plugin_module, plugin_class_name)
                        
                        # Full Resource Manifest Auto-Discovery
                        manifest = getattr(plugin_cls, "manifest", None)
                        if manifest:
                            if manifest.locales and loc_manager:
                                plugin_locales = plugin_path / manifest.locales
                                if plugin_locales.exists() and plugin_locales.is_dir():
                                    loc_manager.add_locales_directory(plugin_locales)
                                    
                            # Future: auto-register graphs, assets, components...
                            
                        else:
                            # Fallback legacy
                            if loc_manager:
                                plugin_locales = plugin_path / "locales"
                                if plugin_locales.exists():
                                    loc_manager.add_locales_directory(plugin_locales)
                        
                        if hasattr(plugin_cls, "initialize"):
                            # Some plugins might need context now
                            import inspect
                            sig = inspect.signature(plugin_cls.initialize)
                            if "context" in sig.parameters:
                                plugin_cls.initialize(context=context)
                            else:
                                plugin_cls.initialize()
                            
                        self.loaded_plugins.append(plugin_class_name)
                        
                        # Auto-discover metadata definitions inside the plugin module
                        if context:
                            from engine.metadata.manager import MetadataManager
                            meta_manager = context.services.get_optional(MetadataManager)
                            if meta_manager:
                                for name in dir(plugin_module):
                                    obj = getattr(plugin_module, name)
                                    if hasattr(obj, "__node_definition__"):
                                        meta_manager.register(getattr(obj, "__node_definition__"))
                                        
                                # Also check submodules like .nodes if they exist
                                if hasattr(plugin_module, "nodes"):
                                    nodes_mod = getattr(plugin_module, "nodes")
                                    for name in dir(nodes_mod):
                                        obj = getattr(nodes_mod, name)
                                        if hasattr(obj, "__node_definition__"):
                                            meta_manager.register(getattr(obj, "__node_definition__"))
                                            
                except Exception as e:
                    print(f"Failed to load plugin {full_module_name}: {e}")
