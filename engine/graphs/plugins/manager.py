"""Plugin Manager for dynamic loading (IService)."""
import importlib
import pkgutil
from pathlib import Path
from engine.core.services import EngineServices, IService

class PluginManager(IService):
    """Discovers and initializes engine plugins."""
    
    def __init__(self):
        super().__init__()
        self._initialized = False
        
    def initialize(self, context=None) -> None:
        if self._initialized: return
        self.load_all_plugins(context=context)
        self._initialized = True
        
    def shutdown(self) -> None:
        self._initialized = False
    
    @property
    def loaded_plugins(self):
        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.plugin import PluginDefinition
        
        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                return [p.id for p in manager.get_all(PluginDefinition)]
        return []

    def load_all_plugins(self, plugins_package="engine.plugins", context=None):
        try:
            package = importlib.import_module(plugins_package)
        except ImportError:
            return
            
        if not hasattr(package, "__path__"):
            return
            
        # Needs LocalizationManager if we register locales
        loc_manager = None
        meta_manager = None
        if context:
            from engine.localization import LocalizationManager
            from engine.metadata.manager import MetadataManager
            loc_manager = context.services.get_optional(LocalizationManager)
            meta_manager = context.services.get_optional(MetadataManager)
            
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                full_module_name = f"{plugins_package}.{module_name}"
                try:
                    plugin_module = importlib.import_module(full_module_name)
                    plugin_path = Path(plugin_module.__file__).parent
                    
                    plugin_class_name = module_name.capitalize() + "Plugin"
                    if hasattr(plugin_module, plugin_class_name):
                        plugin_cls = getattr(plugin_module, plugin_class_name)
                        
                        plugin_def = None
                        if meta_manager:
                            from engine.core.metadata.plugin import PluginDefinition
                            plugin_def = PluginDefinition(
                                id=module_name,
                                title_key=f"plugin.{module_name}.title",
                                module_name=full_module_name,
                                entry_point=plugin_class_name
                            )
                        
                        # Full Resource Manifest Auto-Discovery
                        manifest = getattr(plugin_cls, "manifest", None)
                        if manifest:
                            if plugin_def:
                                plugin_def.version = getattr(manifest, "version", "1.0.0")
                                plugin_def.author = getattr(manifest, "author", "Unknown")
                                
                            if manifest.locales and loc_manager:
                                plugin_locales = plugin_path / manifest.locales
                                if plugin_locales.exists() and plugin_locales.is_dir():
                                    loc_manager.add_locales_directory(plugin_locales)
                                    
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
                            
                        if meta_manager and plugin_def:
                            meta_manager.register(plugin_def)
                        
                        # Auto-discover metadata definitions inside the plugin module
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
