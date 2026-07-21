from pathlib import Path


WORKFLOW = Path(".github/workflows/python-tests.yml")


def test_ci_enforces_critical_boundary_coverage() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "critical-coverage:" in source
    assert "--cov=." in source
    assert "--fail-under=70" in source
    for boundary in (
        "engine/scene/scene_document.py",
        "engine/runtime/lifecycle_scheduler.py",
        "engine/runtime/runtime_world.py",
        "engine/logic/runtime/*.py",
        "editor/runtime/viewport_session.py",
        "editor/asset_browser_controller.py",
        "editor/inspector_controller.py",
    ):
        assert boundary in source
