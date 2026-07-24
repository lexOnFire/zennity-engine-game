from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from engine.packages.package import Package


class PackageRegistry:
    """Manages the registration and discovery of installed packages."""

    def __init__(self, packages_dir: Path) -> None:
        self.packages_dir = Path(packages_dir).resolve()
        self._packages: Dict[str, Package] = {}

    def scan(self) -> List[Package]:
        """Scans packages_dir for any subdirectory containing package.json."""
        self._packages.clear()
        if not self.packages_dir.exists():
            return []

        for p_dir in self.packages_dir.iterdir():
            if p_dir.is_dir():
                manifest_path = p_dir / "package.json"
                if manifest_path.exists():
                    try:
                        pkg = Package.from_manifest(manifest_path)
                        self.register_package(pkg)
                    except Exception:
                        # Log error or skip invalid packages silently to avoid breaking execution
                        pass

        return self.list_packages()

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
        """Returns all registered packages sorted by name."""
        return sorted(self._packages.values(), key=lambda p: p.name)
