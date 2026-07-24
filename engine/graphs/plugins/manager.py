"""Plugin Manager for dynamic loading."""
import importlib
import pkgutil
from pathlib import Path
from engine.localization import LocalizationManager

class PluginManager:
    """Discovers and initializes engine plugins."""
    
    @classmethod
    def load_all_plugins(cls, plugins_package="engine.plugins"):
        try:
            package = importlib.import_module(plugins_package)
        except ImportError:
            return
            
        if not hasattr(package, "__path__"):
            return
            
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                full_module_name = f"{plugins_package}.{module_name}"
                try:
                    plugin_module = importlib.import_module(full_module_name)
                    plugin_path = Path(plugin_module.__file__).parent
                    
                    plugin_class_name = module_name.capitalize() + "Plugin"
                    if hasattr(plugin_module, plugin_class_name):
                        plugin_cls = getattr(plugin_module, plugin_class_name)
                        
                        # Phase 6: Use PluginManifest if available
                        manifest = getattr(plugin_cls, "manifest", None)
                        if manifest and manifest.locales:
                            plugin_locales = plugin_path / manifest.locales
                            if plugin_locales.exists() and plugin_locales.is_dir():
                                LocalizationManager().add_locales_directory(plugin_locales)
                        else:
                            # Fallback legacy discovery
                            plugin_locales = plugin_path / "locales"
                            if plugin_locales.exists() and plugin_locales.is_dir():
                                LocalizationManager().add_locales_directory(plugin_locales)
                        
                        if hasattr(plugin_cls, "initialize"):
                            plugin_cls.initialize()
                except Exception as e:
                    print(f"Failed to load plugin {full_module_name}: {e}")
