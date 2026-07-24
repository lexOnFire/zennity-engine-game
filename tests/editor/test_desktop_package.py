from __future__ import annotations

from engine.build import (
    BuildConfig,
    BuildTarget,
    DesktopPackagePlan,
    ExportProfile,
    create_desktop_package_plan,
    create_plan_from_profile,
)


def test_desktop_package_plan_for_windows() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.WINDOWS, output_dir="dist")

    plan = create_desktop_package_plan(config)

    assert plan.project_name == "Demo"
    assert plan.target == BuildTarget.WINDOWS
    assert plan.executable_name == "Demo.exe"
    assert plan.root_dir.replace("\\", "/") == "dist/windows/Demo"
    assert any(path.replace("\\", "/").endswith("Data") for path in plan.directories)
    assert any(path.replace("\\", "/").endswith("Runtime") for path in plan.directories)


def test_desktop_package_plan_for_linux() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.LINUX)

    plan = create_desktop_package_plan(config)

    assert plan.executable_name == "Demo"


def test_desktop_package_plan_for_macos() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.MACOS)

    plan = create_desktop_package_plan(config)

    assert plan.executable_name == "Demo.app"


def test_desktop_package_plan_includes_entry_scene() -> None:
    config = BuildConfig(project_name="Demo", entry_scene="Scenes/Main.zscene")

    plan = create_desktop_package_plan(config)

    assert any(path.replace("\\", "/").endswith("Data/Main.zscene") for path in plan.files)


def test_desktop_package_plan_can_skip_assets() -> None:
    config = BuildConfig(project_name="Demo", include_assets=False)

    plan = create_desktop_package_plan(config)

    assert not any(path.replace("\\", "/").endswith("Assets") for path in plan.directories)


def test_desktop_package_plan_roundtrip() -> None:
    config = BuildConfig(project_name="Demo", target=BuildTarget.LINUX)
    plan = create_desktop_package_plan(config)

    restored = DesktopPackagePlan.from_dict(plan.to_dict())

    assert restored.to_dict() == plan.to_dict()


def test_desktop_package_plan_from_profile() -> None:
    profile = ExportProfile(name="Linux", config=BuildConfig(project_name="Demo", target=BuildTarget.LINUX))

    plan = create_plan_from_profile(profile)

    assert plan.project_name == "Demo"
    assert plan.target == BuildTarget.LINUX
