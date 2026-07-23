import json
import pytest
import shutil
from pathlib import Path
from engine.packages.manager import PackageManager
from engine.packages.registry import PackageRegistry
from engine.project_templates import create_project

@pytest.fixture
def temp_project(tmp_path: Path):
    project_dir = tmp_path / "TestProject"
    create_project("empty", project_dir)
    return project_dir

@pytest.fixture
def mock_plugin_src(tmp_path: Path):
    plugin_dir = tmp_path / "mock_plugin"
    plugin_dir.mkdir()
    
    # Write package.json
    manifest = {
        "name": "mock_plugin",
        "version": "1.0.0",
        "engine_version": "1.2.0",
        "inspector_plugins": ["mock_plugin.plugins.MockInspectorPlugin"],
        "editor_extensions": ["mock_plugin.extensions.MockEditorExtension"]
    }
    with open(plugin_dir / "package.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)
        
    # Write code
    (plugin_dir / "plugins.py").write_text('''
class MockInspectorPlugin:
    component_type = "MockComponent"
    def supports(self, component): return True
''', encoding="utf-8")

    (plugin_dir / "extensions.py").write_text('''
class MockEditorExtension:
    name = "mock_ext"
    def install(self, editor): pass
    def uninstall(self, editor): pass
''', encoding="utf-8")

    return plugin_dir


def test_transactional_install_and_uninstall(temp_project: Path, mock_plugin_src: Path):
    manager = PackageManager(temp_project)
    
    # Install
    pkg = manager.install_local_package(mock_plugin_src)
    assert pkg.name == "mock_plugin"
    assert len(manager.registry.list_packages()) == 1
    
    dest_dir = manager.packages_dir / "mock_plugin"
    assert dest_dir.exists()
    
    # Test class resolution
    plugin_class = manager.registry.resolve_class(pkg.inspector_plugins[0])
    assert plugin_class is not None
    assert plugin_class.__name__ == "MockInspectorPlugin"
    
    # Uninstall
    manager.uninstall_package("mock_plugin")
    assert not dest_dir.exists()
    assert len(manager.registry.list_packages()) == 0


def test_invalid_class_resolution(temp_project: Path, mock_plugin_src: Path):
    manager = PackageManager(temp_project)
    pkg = manager.install_local_package(mock_plugin_src)
    
    # Test safe failure
    result = manager.registry.resolve_class("mock_plugin.plugins.NonExistentClass")
    assert result is None
