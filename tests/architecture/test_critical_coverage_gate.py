from pathlib import Path


WORKFLOW = Path(".github/workflows/python-tests.yml")


CRITICAL_BOUNDARIES = (
    "engine/scene/scene_document.py",
    "engine/runtime/lifecycle_scheduler.py",
    "engine/runtime/runtime_world.py",
    "engine/logic/runtime/*.py",
    "engine/logic/runtime/nodes/*.py",
    "editor/runtime/isolated_play_mode_controller.py",
)

UI_INTEGRATION_MODULES = (
    "editor/runtime/viewport_session.py",
    "editor/asset_browser_controller.py",
    "editor/console_controller.py",
    "editor/hierarchy_controller.py",
    "editor/inspector_controller.py",
)


def test_ci_enforces_critical_boundary_coverage() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "critical-coverage:" in source
    assert "--cov=engine --cov=editor" in source
    assert "--fail-under=70" in source
    assert "release/v1.0.0-rc2" in source

    for boundary in CRITICAL_BOUNDARIES:
        assert boundary in source


def test_critical_gate_excludes_ui_integration_modules() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    include_definition = source.split("INCLUDE=", maxsplit=1)[1].splitlines()[0]

    for module in UI_INTEGRATION_MODULES:
        assert module not in include_definition
