"""Plugin Manager for dynamic loading."""
import importlib
import pkgutil
from pathlib import Path

class PluginManager:
    """Discovers and initializes engine plugins."""
    
    @classmethod
    def load_all_plugins(cls, plugins_package="engine.plugins"):
        """Dynamically imports all modules in the plugins directory."""
        try:
            package = importlib.import_module(plugins_package)
        except ImportError:
            print(f"Warning: Plugin package {plugins_package} not found.")
            return
            
        if not hasattr(package, "__path__"):
            return
            
        for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                full_module_name = f"{plugins_package}.{module_name}"
                try:
                    plugin_module = importlib.import_module(full_module_name)
                    
                    # Assume convention: a plugin exposes an initialize() method or a Plugin class
                    # For now, we will look for an explicit Plugin class matching the naming convention,
                    # e.g., engine.plugins.logic exposes LogicPlugin.
                    plugin_class_name = module_name.capitalize() + "Plugin"
                    if hasattr(plugin_module, plugin_class_name):
                        plugin_cls = getattr(plugin_module, plugin_class_name)
                        if hasattr(plugin_cls, "initialize"):
                            plugin_cls.initialize()
                except Exception as e:
                    print(f"Failed to load plugin {full_module_name}: {e}")
