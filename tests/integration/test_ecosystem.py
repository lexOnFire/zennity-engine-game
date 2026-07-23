import json
import pytest
from pathlib import Path
from engine.packages.manager import PackageManager
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
    def load(self, editor): pass
    def enable(self, editor): pass
    def disable(self, editor): pass
    def unload(self, editor): pass
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

    # Test lockfile
    lockfile = manager.packages_dir / "packages.lock.json"
    assert lockfile.exists()

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
    manager.install_local_package(mock_plugin_src)

    # Test safe failure
    result = manager.registry.resolve_class("mock_plugin.plugins.NonExistentClass")
    assert result is None


def test_missing_dependency_rollback(temp_project: Path, mock_plugin_src: Path):
    manager = PackageManager(temp_project)

    # Add a missing dependency to the manifest
    manifest_path = mock_plugin_src / "package.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["dependencies"] = {"non_existent_package": "1.0.0"}
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    with pytest.raises(RuntimeError, match="installed but failed registry load"):
        manager.install_local_package(mock_plugin_src)

    assert len(manager.registry.list_packages()) == 0
    assert not (manager.packages_dir / "mock_plugin").exists()


def test_path_traversal_prevention(temp_project: Path, mock_plugin_src: Path):
    manager = PackageManager(temp_project)

    # Try to set a malicious name
    manifest_path = mock_plugin_src / "package.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["name"] = "../malicious_plugin"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    with pytest.raises(ValueError, match="Invalid package name"):
        manager.install_local_package(mock_plugin_src)


def test_downgrade_prevention(temp_project: Path, mock_plugin_src: Path):
    manager = PackageManager(temp_project)
    manager.install_local_package(mock_plugin_src)

    # Change version to lower
    manifest_path = mock_plugin_src / "package.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["version"] = "0.9.0"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f)

    with pytest.raises(ValueError, match="Cannot downgrade"):
        manager.update_package("mock_plugin", mock_plugin_src)
