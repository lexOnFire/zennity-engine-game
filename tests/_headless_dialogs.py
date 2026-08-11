"""Headless contract for the whole test suite.

PHASE 9.5B Stage 2.1.

Qt's ``QFileDialog`` and ``QMessageBox`` static helpers open a *modal* dialog
and spin their own event loop until a human answers.  Under
``QT_QPA_PLATFORM=offscreen`` there is no human and no window manager, so the
loop never terminates: the test hangs forever, and because the block happens
inside Qt's C++ event loop the process does not even respond to SIGTERM --
``pytest-timeout`` cannot interrupt it and CI has to be killed with SIGKILL.

Two tests hit this through the same call chain::

    test_scale_tool_blocked_during_play_mode          (test_phase1_scale_tool.py)
    test_phase1_play_controls_reflect_simulation_state (test_phase1_editor_context.py)
      -> ZennityPhase1Editor.play()                    phase1_editor.py:370
        -> save_scene()                                phase1_editor.py:376
          -> current_scene_path is None
            -> save_scene_as()                         phase1_editor_scene_ops.py:145
              -> QFileDialog.getSaveFileName(...)      phase1_editor_scene_ops.py:153

Rather than special-case those two, this module makes the whole suite
headless-safe: every blocking entry point is replaced with a deterministic
answer.  21 editor modules call into these APIs, so any new test could otherwise
reintroduce the hang -- and the guard is installed repo-wide rather than under
tests/editor/ because tests outside that directory build editor widgets too
(``tests/integration/test_memory_leak.py`` drives 500 Play/Stop cycles).

The seam is test-only.  No production code is changed, and nothing here builds a
parallel editor architecture -- it patches exactly the Qt functions the editor
already calls.

A test that wants a specific answer overrides it locally with ``monkeypatch``,
which takes precedence over the session default -- see ``headless_dialogs``.

A test whose *subject* is the dialog API itself opts out entirely::

    @pytest.mark.real_dialog
    def test_file_dialog_filters_are_built_correctly():
        ...

The guard then leaves Qt untouched, so future dialog tests are not locked out by
this policy.  Such a test owns its own non-blocking strategy (constructing the
dialog without ``exec()``, or driving it from a QTimer); the marker is an escape
hatch, not a licence to block CI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QFileDialog,
        QMenu,
        QMessageBox,
    )
except ImportError:  # pragma: no cover - Qt is required by the editor suite
    QApplication = QDialog = QFileDialog = QMenu = QMessageBox = None


class HeadlessDialogRecorder:
    """Records the modal calls a test made, and serves canned answers.

    Exposed as the ``headless_dialogs`` fixture so a test can assert that a code
    path *did* prompt, or change what the prompt returns, without reaching for
    the real dialog.
    """

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.calls: list[tuple[str, tuple, dict]] = []
        #: Path handed back by the save/open helpers.  Inside a pytest tmp dir,
        #: so a test that really writes the file cannot touch the repository.
        self.save_path: str = str(directory / "headless_scene.zscene")
        self.open_path: str = str(directory / "headless_scene.zscene")
        self.directory_path: str = str(directory)
        #: Answer returned by QMessageBox helpers.
        self.message_box_answer = None

    def record(self, name: str, args: tuple, kwargs: dict) -> None:
        self.calls.append((name, args, kwargs))

    def called(self, name: str) -> bool:
        return any(call == name for call, _args, _kwargs in self.calls)

    @property
    def call_names(self) -> list[str]:
        return [call for call, _args, _kwargs in self.calls]


@pytest.fixture(scope="session")
def _headless_dialog_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("headless_dialogs")


@pytest.fixture
def headless_dialogs(request) -> HeadlessDialogRecorder:
    """The recorder installed by the autouse guard for this test."""
    return request.getfixturevalue("_headless_dialog_guard")


def pytest_configure(config):  # pragma: no cover - pytest hook
    config.addinivalue_line(
        "markers",
        "real_dialog: opt out of the headless dialog guard; the test exercises "
        "the Qt dialog API itself and owns its own non-blocking strategy.",
    )


@pytest.fixture(autouse=True)
def _headless_dialog_guard(request, monkeypatch, _headless_dialog_dir: Path):
    """Replace every blocking modal entry point with a deterministic answer."""
    if QFileDialog is None:  # pragma: no cover
        yield None
        return
    if request.node.get_closest_marker("real_dialog") is not None:
        yield None
        return

    recorder = HeadlessDialogRecorder(_headless_dialog_dir)

    def _file_answer(name: str, value_attr: str):
        def replacement(*args, **kwargs):
            recorder.record(name, args, kwargs)
            # Qt returns (path, selected_filter) from these helpers.
            return (getattr(recorder, value_attr), "")

        return staticmethod(replacement)

    def _directory_answer(*args, **kwargs):
        recorder.record("getExistingDirectory", args, kwargs)
        return recorder.directory_path

    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", _file_answer("getSaveFileName", "save_path")
    )
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", _file_answer("getOpenFileName", "open_path")
    )
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        staticmethod(
            lambda *a, **k: (recorder.record("getOpenFileNames", a, k), ([recorder.open_path], ""))[1]
        ),
    )
    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", staticmethod(_directory_answer)
    )

    # An instantiated QFileDialog/QDialog blocks the same way via exec().
    def _rejected(self, *args, **kwargs):
        recorder.record(f"{type(self).__name__}.exec", args, kwargs)
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(QDialog, "exec", _rejected, raising=False)
    monkeypatch.setattr(QDialog, "exec_", _rejected, raising=False)
    monkeypatch.setattr(QDialog, "open", lambda self, *a, **k: None, raising=False)

    # QMenu.exec spins its own loop waiting for a click, and QApplication.exec
    # never returns until quit() -- both hang a headless run just as hard.
    if QMenu is not None:
        def _no_menu(self, *args, **kwargs):
            recorder.record("QMenu.exec", args, kwargs)
            return None

        monkeypatch.setattr(QMenu, "exec", _no_menu, raising=False)
        monkeypatch.setattr(QMenu, "exec_", _no_menu, raising=False)

    if QApplication is not None:
        def _no_app_loop(*args, **kwargs):
            raise AssertionError(
                "a test called QApplication.exec(); that blocks until quit() and "
                "will hang CI. Drive the widget directly instead."
            )

        monkeypatch.setattr(QApplication, "exec", staticmethod(_no_app_loop), raising=False)
        monkeypatch.setattr(QApplication, "exec_", staticmethod(_no_app_loop), raising=False)

    if QMessageBox is not None:
        default_answers = {
            "question": QMessageBox.StandardButton.No,
            "warning": QMessageBox.StandardButton.Ok,
            "information": QMessageBox.StandardButton.Ok,
            "critical": QMessageBox.StandardButton.Ok,
            "about": None,
            "aboutQt": None,
        }
        for name, answer in default_answers.items():
            def make(name=name, answer=answer):
                def replacement(*args, **kwargs):
                    recorder.record(f"QMessageBox.{name}", args, kwargs)
                    if recorder.message_box_answer is not None:
                        return recorder.message_box_answer
                    return answer

                return staticmethod(replacement)

            monkeypatch.setattr(QMessageBox, name, make(), raising=False)

    yield recorder
