"""Keep package and serialized-asset versions aligned for releases."""

from pathlib import Path

import editor
import engine
from engine.prefabs.prefab_format import ENGINE_VERSION

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_public_versions_match_package_metadata() -> None:
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    package_version = project["project"]["version"]

    assert package_version == "1.0.1"
    assert engine.__version__ == package_version
    assert editor.__version__ == package_version
    assert ENGINE_VERSION == package_version
