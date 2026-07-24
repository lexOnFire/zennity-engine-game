from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .build_config import BuildConfig, BuildTarget


@dataclass
class ExportProfile:
    name: str = "Debug"
    description: str = ""
    config: BuildConfig = field(default_factory=BuildConfig)
    tags: list[str] = field(default_factory=list)
    enabled: bool = True

    def normalized_name(self) -> str:
        value = str(self.name or "Debug").strip()
        return value or "Debug"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.normalized_name():
            errors.append("profile name is required")
        errors.extend(self.config.validate())
        return errors

    def to_config(self) -> BuildConfig:
        return BuildConfig.from_dict(self.config.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.normalized_name(),
            "description": str(self.description or ""),
            "config": self.config.to_dict(),
            "tags": [str(tag) for tag in self.tags],
            "enabled": bool(self.enabled),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ExportProfile":
        if not data:
            return cls()
        tags = data.get("tags", [])
        if type(tags) is not list:
            tags = []
        return cls(
            name=str(data.get("name", "Debug") or "Debug"),
            description=str(data.get("description", "") or ""),
            config=BuildConfig.from_dict(data.get("config", {})),
            tags=[str(tag) for tag in tags],
            enabled=bool(data.get("enabled", True)),
        )


def debug_profile() -> ExportProfile:
    return ExportProfile(
        name="Debug",
        description="Development export profile",
        config=BuildConfig(project_name="ZennityGame", target=BuildTarget.WINDOWS, development=True),
        tags=["debug", "development"],
    )


def release_profile() -> ExportProfile:
    return ExportProfile(
        name="Release",
        description="Release export profile",
        config=BuildConfig(project_name="ZennityGame", target=BuildTarget.WINDOWS, development=False),
        tags=["release"],
    )
