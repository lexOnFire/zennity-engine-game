"""Characterization tests for the public Phase 1 editor entrypoint.

These tests intentionally avoid importing Qt.  Their job is to freeze the
bootstrap contract before the editor shells are consolidated.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from editor import phase1_main


ROOT = Path(__file__).resolve().parents[2]


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    for attribute, value in attributes.items():
        setattr(module, attribute, value)
    return module


def test_default_entrypoint_delegates_to_isolated_editor(monkeypatch) -> None:
    calls: list[str] = []
    isolated = _module(
        "editor.isolated_editor_main",
        main=lambda: calls.append("isolated"),
    )

    monkeypatch.setitem(sys.modules, "editor.isolated_editor_main", isolated)
    monkeypatch.setattr(sys, "argv", ["editor.phase1_main"])

    phase1_main.main()

    assert calls == ["isolated"]


def test_default_entrypoint_does_not_import_legacy_editor(monkeypatch) -> None:
    isolated = _module("editor.isolated_editor_main", main=lambda: None)
    monkeypatch.setitem(sys.modules, "editor.isolated_editor_main", isolated)
    monkeypatch.delitem(sys.modules, "editor.phase1_editor", raising=False)
    monkeypatch.setattr(sys, "argv", ["editor.phase1_main"])

    phase1_main.main()

    assert "editor.phase1_editor" not in sys.modules


def test_legacy_flag_starts_only_embedded_editor(monkeypatch) -> None:
    calls: list[object] = []

    class FakeApplication:
        def __init__(self, argv) -> None:
            calls.append(("application", list(argv)))

        def setStyleSheet(self, stylesheet: str) -> None:
            calls.append(("stylesheet", stylesheet))

        def exec(self) -> int:
            calls.append("exec")
            return 17

    class FakeWindow:
        def __init__(self) -> None:
            calls.append("window")

        def show(self) -> None:
            calls.append("show")

    qt_widgets = _module("PySide6.QtWidgets", QApplication=FakeApplication)
    pyside = _module("PySide6", QtWidgets=qt_widgets)
    legacy = _module("editor.phase1_editor", ZennityPhase1Editor=FakeWindow)
    theme = _module("editor.premium_theme", PREMIUM_QSS="phase-1-theme")
    isolated = _module(
        "editor.isolated_editor_main",
        main=lambda: calls.append("isolated"),
    )

    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", qt_widgets)
    monkeypatch.setitem(sys.modules, "editor.phase1_editor", legacy)
    monkeypatch.setitem(sys.modules, "editor.premium_theme", theme)
    monkeypatch.setitem(sys.modules, "editor.isolated_editor_main", isolated)
    monkeypatch.setattr(
        sys,
        "argv",
        ["editor.phase1_main", "--legacy-embedded"],
    )

    with pytest.raises(SystemExit) as exit_info:
        phase1_main.main()

    assert exit_info.value.code == 17
    assert calls == [
        ("application", ["editor.phase1_main", "--legacy-embedded"]),
        ("stylesheet", "phase-1-theme"),
        "window",
        "show",
        "exec",
    ]


def test_bootstrap_errors_are_not_silenced(monkeypatch) -> None:
    def fail_to_start() -> None:
        raise RuntimeError("viewport bootstrap failed")

    isolated = _module("editor.isolated_editor_main", main=fail_to_start)
    monkeypatch.setitem(sys.modules, "editor.isolated_editor_main", isolated)
    monkeypatch.setattr(sys, "argv", ["editor.phase1_main"])

    with pytest.raises(RuntimeError, match="viewport bootstrap failed"):
        phase1_main.main()


def test_package_command_points_to_official_entrypoint() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["scripts"] == {
        "zennity-editor": "editor.phase1_main:main",
    }


def test_readme_uses_only_official_public_launch_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "python -m editor.phase1_main" in readme
    assert "zennity-editor" in readme
    assert "python editor/main.py" not in readme
