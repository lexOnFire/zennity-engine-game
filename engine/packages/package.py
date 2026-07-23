from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


class Package:
    """Represents a Zennity Engine Package and its manifest metadata."""

    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        description: str,
        engine_version_min: str,
        engine_version_max: str,
        dependencies: Dict[str, str],
        capabilities: List[str],
        components: List[str],
        inspector_plugins: List[str],
        editor_extensions: List[str],
        importers: List[str],
        gizmos: List[str],
        content_dir: Path,
    ) -> None:
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.engine_version_min = engine_version_min
        self.engine_version_max = engine_version_max
        self.dependencies = dependencies
        self.capabilities = capabilities
        self.components = components
        self.inspector_plugins = inspector_plugins
        self.editor_extensions = editor_extensions
        self.importers = importers
        self.gizmos = gizmos
        self.content_dir = content_dir

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> Package:
        """Loads and validates a package from a manifest file (package.json)."""
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in manifest {manifest_path}: {e}")

        cls.validate_manifest_data(data)

        # Tratar engine_version legacy
        engine_ver = str(data.get("engine_version", "1.0.0"))

        return cls(
            name=str(data["name"]),
            version=str(data["version"]),
            author=str(data.get("author", "")),
            description=str(data.get("description", "")),
            engine_version_min=str(data.get("engine_version_min", engine_ver)),
            engine_version_max=str(data.get("engine_version_max", "")),
            dependencies=dict(data.get("dependencies", {})),
            capabilities=list(data.get("capabilities", [])),
            components=list(data.get("components", [])),
            inspector_plugins=list(data.get("inspector_plugins", [])),
            editor_extensions=list(data.get("editor_extensions", [])),
            importers=list(data.get("importers", [])),
            gizmos=list(data.get("gizmos", [])),
            content_dir=manifest_path.parent,
        )

    @staticmethod
    def validate_manifest_data(data: Dict[str, Any]) -> None:
        """Validates mandatory fields inside manifest JSON and applies security constraints."""
        required = ["name", "version"]
        for field in required:
            if field not in data or not data[field]:
                raise ValueError(f"Missing mandatory field: '{field}'")

        name = str(data["name"])
        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", name) or name in (".", "..") or ".." in name:
            raise ValueError(f"Invalid package name '{name}'. Only alphanumeric characters, dashes, underscores and dots are allowed to prevent path traversal.")

        # Simple semver validation
        version = str(data["version"])
        parts = version.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid version format '{version}'. Must be basic semver (e.g. 1.0.0)")
