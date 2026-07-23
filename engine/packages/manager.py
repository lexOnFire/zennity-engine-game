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
        temp_dir = self.packages_dir / f".temp_{source_pkg.name}"
        backup_dir = self.packages_dir / f".backup_{source_pkg.name}"
        
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        
        # Cleanup temp artifacts from previous failed runs
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        try:
            # 1. Copy to temp dir first
            shutil.copytree(source_path, temp_dir)
            
            # 2. Backup existing
            if dest_dir.exists():
                dest_dir.rename(backup_dir)
                
            # 3. Swap temp to final
            temp_dir.rename(dest_dir)
            
            # 4. Remove backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        except Exception as e:
            # Rollback
            if dest_dir.exists() and temp_dir.exists():  # If swap partially failed? Unlikely but safe.
                shutil.rmtree(dest_dir)
            if backup_dir.exists():
                backup_dir.rename(dest_dir)
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise RuntimeError(f"Package installation failed, rolled back. Error: {e}")

        # Re-scan/load from destination
        installed_manifest = dest_dir / "package.json"
        installed_pkg = Package.from_manifest(installed_manifest)
        self.registry.register_package(installed_pkg)
        
        return installed_pkg

    def uninstall_package(self, name: str) -> bool:
        """Removes an installed package from the disk and registry transactionally."""
        pkg = self.registry.get_package(name)
        if not pkg:
            return False

        dest_dir = self.packages_dir / name
        backup_dir = self.packages_dir / f".backup_{name}"
        
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        if dest_dir.exists():
            try:
                dest_dir.rename(backup_dir)
                shutil.rmtree(backup_dir)
            except Exception as e:
                if backup_dir.exists() and not dest_dir.exists():
                    backup_dir.rename(dest_dir)
                raise RuntimeError(f"Package uninstallation failed. Error: {e}")

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
