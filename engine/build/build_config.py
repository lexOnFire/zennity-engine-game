from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class BuildTarget(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    WEB = "web"


@dataclass
class BuildConfig:
    project_name: str = "ZennityGame"
    target: BuildTarget = BuildTarget.WINDOWS
    entry_scene: str = ""
    output_dir: str = "Builds"
    include_assets: bool = True
    development: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def normalized_project_name(self) -> str:
        name = str(self.project_name or "ZennityGame").strip()
        return name or "ZennityGame"

    def normalized_output_dir(self) -> str:
        value = str(self.output_dir or "Builds").strip()
        return value or "Builds"

    def target_value(self) -> str:
        return self.target.value if hasattr(self.target, "value") else str(self.target)

    def output_path(self) -> Path:
        return Path(self.normalized_output_dir()) / self.target_value() / self.normalized_project_name()

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.target_value():
            errors.append("target is required")
        if self.entry_scene and not str(self.entry_scene).lower().endswith((".zscene", ".json")):
            errors.append("entry_scene must be a scene file")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.normalized_project_name(),
            "target": self.target_value(),
            "entry_scene": str(self.entry_scene or ""),
            "output_dir": self.normalized_output_dir(),
            "include_assets": bool(self.include_assets),
            "development": bool(self.development),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "BuildConfig":
        if not data:
            return cls()
        raw_target = str(data.get("target", BuildTarget.WINDOWS.value) or BuildTarget.WINDOWS.value).lower()
        try:
            target = BuildTarget(raw_target)
        except ValueError:
            target = BuildTarget.WINDOWS
        metadata = data.get("metadata", {})
        if type(metadata) is not dict:
            metadata = {}
        return cls(
            project_name=str(data.get("project_name", "ZennityGame") or "ZennityGame"),
            target=target,
            entry_scene=str(data.get("entry_scene", "") or ""),
            output_dir=str(data.get("output_dir", "Builds") or "Builds"),
            include_assets=bool(data.get("include_assets", True)),
            development=bool(data.get("development", True)),
            metadata=dict(metadata),
        )
