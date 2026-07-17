from __future__ import annotations

from engine.build import BuildConfig, BuildTarget, ExportProfile, ExportProfileManager
from engine.build.export_profile import debug_profile, release_profile


def test_export_profile_defaults_are_valid() -> None:
    profile = ExportProfile()

    assert profile.normalized_name() == "Debug"
    assert profile.validate() == []
    assert profile.to_config().target == BuildTarget.WINDOWS


def test_export_profile_roundtrip_preserves_config() -> None:
    profile = ExportProfile(
        name="Linux Release",
        description="Linux export",
        config=BuildConfig(project_name="Demo", target=BuildTarget.LINUX, entry_scene="main.zscene"),
        tags=["linux", "release"],
        enabled=False,
    )

    restored = ExportProfile.from_dict(profile.to_dict())

    assert restored.to_dict() == profile.to_dict()
    assert restored.to_config().project_name == "Demo"
    assert restored.to_config().target == BuildTarget.LINUX


def test_default_profiles_have_expected_modes() -> None:
    debug = debug_profile()
    release = release_profile()

    assert debug.config.development is True
    assert release.config.development is False


def test_export_profile_manager_register_get_remove() -> None:
    manager = ExportProfileManager()
    custom = ExportProfile(name="Web", config=BuildConfig(target=BuildTarget.WEB))

    manager.register(custom)

    assert "Web" in manager.names()
    assert manager.get("Web").config.target == BuildTarget.WEB
    assert manager.remove("Web") is True
    assert manager.get("Web") is None


def test_export_profile_manager_enabled_profiles() -> None:
    manager = ExportProfileManager()
    manager.register(ExportProfile(name="Disabled", enabled=False))

    names = [profile.name for profile in manager.enabled_profiles()]

    assert "Debug" in names
    assert "Release" in names
    assert "Disabled" not in names


def test_export_profile_manager_dict_roundtrip() -> None:
    manager = ExportProfileManager()
    manager.register(ExportProfile(name="Linux", config=BuildConfig(target=BuildTarget.LINUX)))

    restored = ExportProfileManager.from_dict(manager.to_dict())

    assert restored.names() == manager.names()
    assert restored.get("Linux").config.target == BuildTarget.LINUX


def test_export_profile_manager_file_roundtrip(tmp_path) -> None:
    path = tmp_path / "profiles.json"
    manager = ExportProfileManager()
    manager.register(ExportProfile(name="Mac", config=BuildConfig(target=BuildTarget.MACOS)))

    manager.save(path)
    restored = ExportProfileManager.load(path)

    assert restored.get("Mac").config.target == BuildTarget.MACOS
