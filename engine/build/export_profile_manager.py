from __future__ import annotations

import json
from pathlib import Path

from .export_profile import ExportProfile, debug_profile, release_profile


class ExportProfileManager:
    def __init__(self) -> None:
        self._profiles: dict[str, ExportProfile] = {}
        self.register(debug_profile())
        self.register(release_profile())

    def register(self, profile: ExportProfile) -> None:
        name = profile.normalized_name()
        self._profiles[name] = ExportProfile.from_dict(profile.to_dict())

    def remove(self, name: str) -> bool:
        key = str(name or "").strip()
        if key in self._profiles:
            del self._profiles[key]
            return True
        return False

    def get(self, name: str) -> ExportProfile | None:
        profile = self._profiles.get(str(name or "").strip())
        if profile is None:
            return None
        return ExportProfile.from_dict(profile.to_dict())

    def names(self) -> list[str]:
        return sorted(self._profiles.keys())

    def profiles(self) -> list[ExportProfile]:
        return [ExportProfile.from_dict(self._profiles[name].to_dict()) for name in self.names()]

    def enabled_profiles(self) -> list[ExportProfile]:
        return [profile for profile in self.profiles() if profile.enabled]

    def to_dict(self) -> dict[str, object]:
        return {"profiles": [profile.to_dict() for profile in self.profiles()]}

    @classmethod
    def from_dict(cls, data: dict[str, object] | None) -> "ExportProfileManager":
        manager = cls()
        manager._profiles.clear()
        if not data:
            manager.register(debug_profile())
            manager.register(release_profile())
            return manager
        raw_profiles = data.get("profiles", [])
        if type(raw_profiles) is not list:
            raw_profiles = []
        for item in raw_profiles:
            if type(item) is dict:
                manager.register(ExportProfile.from_dict(item))
        if not manager._profiles:
            manager.register(debug_profile())
            manager.register(release_profile())
        return manager

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "ExportProfileManager":
        source = Path(path)
        if not source.exists():
            return cls()
        data = json.loads(source.read_text(encoding="utf-8"))
        if type(data) is not dict:
            return cls()
        return cls.from_dict(data)
