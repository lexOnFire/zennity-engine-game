from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .build_config import BuildConfig, BuildTarget
from .export_profile import ExportProfile


@dataclass
class DesktopPackagePlan:
    project_name: str
    target: BuildTarget
    root_dir: str
    executable_name: str
    directories: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    include_assets: bool = True
    development: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "target": self.target.value,
            "root_dir": self.root_dir,
            "executable_name": self.executable_name,
            "directories": list(self.directories),
            "files": list(self.files),
            "include_assets": bool(self.include_assets),
            "development": bool(self.development),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DesktopPackagePlan":
        target_value = str(data.get("target", BuildTarget.WINDOWS.value))
        try:
            target = BuildTarget(target_value)
        except ValueError:
            target = BuildTarget.WINDOWS
        return cls(
            project_name=str(data.get("project_name", "ZennityGame")),
            target=target,
            root_dir=str(data.get("root_dir", "")),
            executable_name=str(data.get("executable_name", "ZennityGame")),
            directories=[str(item) for item in data.get("directories", [])],
            files=[str(item) for item in data.get("files", [])],
            include_assets=bool(data.get("include_assets", True)),
            development=bool(data.get("development", True)),
        )


def executable_name_for(config: BuildConfig) -> str:
    name = config.normalized_project_name()
    if config.target == BuildTarget.WINDOWS:
        return f"{name}.exe"
    if config.target == BuildTarget.MACOS:
        return f"{name}.app"
    return name


def create_desktop_package_plan(config: BuildConfig) -> DesktopPackagePlan:
    root = config.output_path()
    directories = [str(root), str(root / "Data"), str(root / "Runtime")]
    files = [str(root / "package_manifest.json")]
    if config.entry_scene:
        files.append(str(root / "Data" / Path(config.entry_scene).name))
    if config.include_assets:
        directories.append(str(root / "Assets"))
    return DesktopPackagePlan(
        project_name=config.normalized_project_name(),
        target=config.target,
        root_dir=str(root),
        executable_name=executable_name_for(config),
        directories=directories,
        files=files,
        include_assets=config.include_assets,
        development=config.development,
    )


def create_plan_from_profile(profile: ExportProfile) -> DesktopPackagePlan:
    return create_desktop_package_plan(profile.to_config())
