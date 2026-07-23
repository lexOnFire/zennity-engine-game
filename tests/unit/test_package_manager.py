import pytest
import tempfile
import json
from pathlib import Path

from engine.packages.package import Package
from engine.packages.manager import PackageManager


@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def create_dummy_package(path: Path, name: str, version: str, extra_manifest: dict = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": name,
        "version": version,
        "author": "Test Author",
        "description": "A test package",
        "dependencies": {},
        "components": ["TestComponent"]
    }
    if extra_manifest:
        manifest.update(extra_manifest)
    
    with open(path / "package.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f)
        
    # Write a dummy script file to simulate package contents
    with open(path / "dummy.py", "w") as f:
        f.write("# dummy package content\n")
        
    return path


def test_package_load_and_validate_success(temp_project_dir):
    pkg_dir = create_dummy_package(temp_project_dir / "my_pkg", "com.zennity.test", "1.0.0")
    pkg = Package.from_manifest(pkg_dir / "package.json")
    
    assert pkg.name == "com.zennity.test"
    assert pkg.version == "1.0.0"
    assert pkg.author == "Test Author"
    assert pkg.components == ["TestComponent"]


def test_package_invalid_json(temp_project_dir):
    pkg_dir = temp_project_dir / "invalid_json"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(pkg_dir / "package.json", "w") as f:
        f.write("{invalid json")
        
    with pytest.raises(ValueError, match="Invalid JSON"):
        Package.from_manifest(pkg_dir / "package.json")


def test_package_missing_fields(temp_project_dir):
    pkg_dir = temp_project_dir / "missing_fields"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(pkg_dir / "package.json", "w") as f:
        json.dump({"name": "only-name"}, f) # Missing version
        
    with pytest.raises(ValueError, match="Missing mandatory field: 'version'"):
        Package.from_manifest(pkg_dir / "package.json")


def test_package_manager_install_uninstall(temp_project_dir):
    source_dir = create_dummy_package(temp_project_dir / "source", "com.zennity.move", "1.2.3")
    
    manager = PackageManager(project_root=temp_project_dir)
    pkg = manager.install_local_package(source_dir)
    
    assert pkg.name == "com.zennity.move"
    assert pkg.version == "1.2.3"
    
    # Check that file was copied
    dest_dir = manager.packages_dir / "com.zennity.move"
    assert dest_dir.exists()
    assert (dest_dir / "dummy.py").exists()
    
    # Check scan/listing
    all_pkgs = manager.registry.list_packages()
    assert len(all_pkgs) == 1
    assert all_pkgs[0].name == "com.zennity.move"
    
    # Uninstall
    success = manager.uninstall_package("com.zennity.move")
    assert success is True
    assert not dest_dir.exists()
    assert len(manager.registry.list_packages()) == 0


def test_package_manager_update(temp_project_dir):
    manager = PackageManager(project_root=temp_project_dir)
    
    source_v1 = create_dummy_package(temp_project_dir / "source_v1", "com.zennity.update", "1.0.0")
    manager.install_local_package(source_v1)
    
    # Try updating to v1.1.0
    source_v2 = create_dummy_package(temp_project_dir / "source_v2", "com.zennity.update", "1.1.0")
    pkg = manager.update_package("com.zennity.update", source_v2)
    assert pkg.version == "1.1.0"
    
    # Try downgrading to v0.9.0 (should fail)
    source_v0 = create_dummy_package(temp_project_dir / "source_v0", "com.zennity.update", "0.9.0")
    with pytest.raises(ValueError, match="Cannot downgrade"):
        manager.update_package("com.zennity.update", source_v0)
