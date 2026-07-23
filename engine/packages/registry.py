from __future__ import annotations

from pathlib import Path
import importlib
import logging
import sys
from typing import Any, Dict, List, Set

from engine.packages.package import Package


class PackageRegistry:
    """Manages the registration and discovery of installed packages."""

    def __init__(self, packages_dir: Path) -> None:
        self.packages_dir = Path(packages_dir).resolve()
        self._packages: Dict[str, Package] = {}
        self._loaded_packages: Dict[str, Package] = {}

    def scan(self) -> List[Package]:
        """Scans packages_dir for any subdirectory containing package.json."""
        self._packages.clear()
        self._loaded_packages.clear()
        
        if not self.packages_dir.exists():
            return []

        scanned_packages = []
        for p_dir in self.packages_dir.iterdir():
            if p_dir.is_dir():
                manifest_path = p_dir / "package.json"
                if manifest_path.exists():
                    try:
                        pkg = Package.from_manifest(manifest_path)
                        # Avoid duplicates
                        if pkg.name in self._packages:
                            logging.warning(f"Duplicate package ID '{pkg.name}' ignored at {p_dir}")
                            continue
                        self._packages[pkg.name] = pkg
                        scanned_packages.append(pkg)
                    except Exception as e:
                        logging.error(f"Failed to load package manifest at {manifest_path}: {e}")

        self._resolve_and_load_dependencies()
        return self.list_packages()

    def _resolve_and_load_dependencies(self) -> None:
        """Uses DFS to check for cycles and missing dependencies, populating _loaded_packages."""
        visited: Set[str] = set()
        stack: Set[str] = set()

        def dfs(pkg_name: str) -> bool:
            if pkg_name in stack:
                logging.error(f"Dependency cycle detected involving '{pkg_name}'")
                return False
            if pkg_name in visited:
                return pkg_name in self._loaded_packages

            stack.add(pkg_name)
            
            pkg = self._packages.get(pkg_name)
            if not pkg:
                logging.error(f"Missing dependency: '{pkg_name}'")
                stack.remove(pkg_name)
                return False

            # Check all dependencies of this package
            all_deps_resolved = True
            for dep_name in pkg.dependencies:
                if not dfs(dep_name):
                    all_deps_resolved = False
                    break

            if all_deps_resolved:
                self._loaded_packages[pkg_name] = pkg
            else:
                logging.error(f"Package '{pkg_name}' could not be loaded due to dependency errors.")

            stack.remove(pkg_name)
            visited.add(pkg_name)
            return all_deps_resolved

        for name in list(self._packages.keys()):
            if name not in visited:
                dfs(name)
                
        # Synchronize active packages with successfully loaded ones
        self._packages = dict(self._loaded_packages)

    def register_package(self, package: Package) -> None:
        """Adds a package to the internal catalog."""
        self._packages[package.name] = package

    def unregister_package(self, name: str) -> None:
        """Removes a package from the internal catalog."""
        self._packages.pop(name, None)

    def get_package(self, name: str) -> Package | None:
        """Finds an installed package by its name."""
        return self._packages.get(name)

    def list_packages(self) -> List[Package]:
        """Returns all successfully loaded packages sorted by name."""
        return sorted(self._packages.values(), key=lambda p: p.name)

    def resolve_class(self, class_path: str) -> Any | None:
        """Dynamically loads a class from a package by its string path."""
        if str(self.packages_dir) not in sys.path:
            sys.path.insert(0, str(self.packages_dir))
            
        try:
            module_name, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            return getattr(module, class_name)
        except Exception as e:
            logging.error(f"Failed to load plugin class '{class_path}': {e}")
            return None
