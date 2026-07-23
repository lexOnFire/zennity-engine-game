"""Contracts that keep the pre-v1 CI baseline reproducible."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _workflow() -> str:
    return (ROOT / ".github/workflows/python-tests.yml").read_text(
        encoding="utf-8"
    )


def test_linux_windows_coverage_and_memory_gates_cover_the_suite() -> None:
    workflow = _workflow()

    # Linux matrix, Windows and coverage run the broad suite. The stateful memory
    # budget runs separately so its object-growth baseline starts in a clean process.
    assert workflow.count("run: python -m pytest") == 4
    assert workflow.count("--ignore=tests/integration/test_memory_leak.py") == 3
    assert (
        "run: python -m pytest tests/integration/test_memory_leak.py" in workflow
    )
    assert "Editor memory stability / Python 3.12" in workflow
    assert "tests/editor/test_project_exporter.py" not in workflow
    assert "windows-tests:" in workflow
    assert "Windows / Python 3.12 / Full suite" in workflow


def test_ci_can_be_started_manually_and_cancels_stale_runs() -> None:
    workflow = _workflow()

    assert "workflow_dispatch:" in workflow
    assert "cancel-in-progress: true" in workflow


def test_pytest_has_one_canonical_configuration() -> None:
    pytest_ini = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "QT_QPA_PLATFORM=offscreen" in pytest_ini
    assert "[tool.pytest.ini_options]" not in pyproject
