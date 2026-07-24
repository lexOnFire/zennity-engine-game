from __future__ import annotations

from pathlib import Path
import shutil

from engine.packages.package import Package
from engine.packages.registry import PackageRegistry


class PackageManager:
    """Manages installation, uninstallation, and updates of local packages."""

    def __init__(self, project_root: str | Path | None = None, packages_subdir: str = "Packages") -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.packages_dir = (self.project_root / packages_subdir).resolve()
        self.registry = PackageRegistry(self.packages_dir)
        self.registry.scan()

    def install_local_package(self, source_dir: str | Path) -> Package:
        """Installs a local package by copying its directory to project's Packages/ folder."""
        source_path = Path(source_dir).resolve()
        manifest_path = source_path / "package.json"
        
        # Load and validate source package before doing I/O
        source_pkg = Package.from_manifest(manifest_path)

        # Dest directory: Packages/<package_name>
        dest_dir = self.packages_dir / source_pkg.name
        
        # In case it already exists, clear it
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        self.packages_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, dest_dir)

        # Re-scan/load from destination
        installed_manifest = dest_dir / "package.json"
        installed_pkg = Package.from_manifest(installed_manifest)
        self.registry.register_package(installed_pkg)
        
        return installed_pkg

    def uninstall_package(self, name: str) -> bool:
        """Removes an installed package from the disk and registry."""
        pkg = self.registry.get_package(name)
        if not pkg:
            return False

        dest_dir = self.packages_dir / name
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        self.registry.unregister_package(name)
        return True

    def update_package(self, name: str, source_dir: str | Path) -> Package:
        """Updates an existing package if the source version is equal or greater."""
        existing_pkg = self.registry.get_package(name)
        if not existing_pkg:
            raise ValueError(f"Package '{name}' is not installed. Install it first.")

        source_path = Path(source_dir).resolve()
        source_pkg = Package.from_manifest(source_path / "package.json")

        # Basic SemVer comparison (major.minor.patch string check or split check)
        def parse_ver(v: str) -> tuple[int, ...]:
            try:
                return tuple(int(x) for x in v.split("."))
            except ValueError:
                return (0,)

        if parse_ver(source_pkg.version) < parse_ver(existing_pkg.version):
            raise ValueError(
                f"Cannot downgrade package '{name}' from version {existing_pkg.version} to {source_pkg.version}"
            )

        # Re-install
        return self.install_local_package(source_dir)
