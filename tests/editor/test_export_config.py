from __future__ import annotations

from engine.build.build_config import BuildConfig, BuildTarget


def test_config_defaults_are_valid() -> None:
    config = BuildConfig()
    assert config.project_name == "ZennityGame"
    assert config.target == BuildTarget.WINDOWS
    assert config.validate() == []


def test_config_output_path_contains_target_and_project() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.LINUX, output_dir="dist")
    assert str(config.output_path()).replace("\\", "/") == "dist/linux/Demo"


def test_config_roundtrip() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.MACOS, entry_scene="main.zscene")
    restored = BuildConfig.from_dict(config.to_dict())
    assert restored.to_dict() == config.to_dict()


def test_config_rejects_invalid_entry_scene_extension() -> None:
    config = BuildConfig(entry_scene="main.txt")
    assert config.validate() == ["entry_scene must be a scene file"]
