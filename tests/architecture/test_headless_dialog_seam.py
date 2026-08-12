"""The headless dialog seam is itself under test.

PHASE 9 recovery item 9B, section 15. The seam in ``tests/_headless_dialogs.py``
is what keeps the suite from hanging on a modal opened inside Qt's C++ event
loop, where neither SIGALRM nor SIGTERM is delivered and ``pytest-timeout``
cannot help. It was shipped in Stage 2.1 with no tests of its own, so nothing
would notice if a Qt or PySide upgrade moved an entry point out from under it --
the failure mode is an indefinite hang in CI, not a red test.

Every test here calls the blocking API directly and asserts it *returned*.
Reaching the assertion is most of the proof.
"""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QDialog,
    QFileDialog,
    QMenu,
    QMessageBox,
)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_get_save_file_name_is_intercepted(headless_dialogs, qapp):
    path, selected_filter = QFileDialog.getSaveFileName(None, "Save", "", "*.zscene")
    assert path == headless_dialogs.save_path
    assert selected_filter == ""
    assert headless_dialogs.called("getSaveFileName")


def test_get_open_file_name_is_intercepted(headless_dialogs, qapp):
    path, _ = QFileDialog.getOpenFileName(None, "Open", "", "*.zscene")
    assert path == headless_dialogs.open_path


def test_get_existing_directory_is_intercepted(headless_dialogs, qapp):
    assert QFileDialog.getExistingDirectory(None, "Pick") == headless_dialogs.directory_path


def test_the_answered_path_is_inside_a_temporary_directory(headless_dialogs, tmp_path):
    """A test that really writes the answer must not write into the checkout."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    for answer in (headless_dialogs.save_path, headless_dialogs.open_path):
        with pytest.raises(ValueError):
            Path(answer).resolve().relative_to(repo_root)


def test_message_box_helpers_are_intercepted(headless_dialogs, qapp):
    assert QMessageBox.question(None, "t", "m") == QMessageBox.StandardButton.No
    assert QMessageBox.warning(None, "t", "m") == QMessageBox.StandardButton.Ok
    assert QMessageBox.information(None, "t", "m") == QMessageBox.StandardButton.Ok
    assert QMessageBox.critical(None, "t", "m") == QMessageBox.StandardButton.Ok


def test_the_message_box_answer_is_steerable(headless_dialogs, qapp):
    """A test that needs 'the user said yes' must not need the real dialog."""
    headless_dialogs.message_box_answer = QMessageBox.StandardButton.Yes
    assert QMessageBox.question(None, "t", "m") == QMessageBox.StandardButton.Yes


def test_dialog_exec_is_intercepted(headless_dialogs, qapp):
    dialog = QDialog()
    assert dialog.exec() == QDialog.DialogCode.Rejected
    assert any(name.endswith(".exec") for name in headless_dialogs.call_names)


def test_menu_exec_is_intercepted(headless_dialogs, qapp):
    """QMenu is the one API that cannot be neutralised by setattr.

    ``QMenu.exec = replacement`` appears to take -- the class attribute really
    does change -- but Shiboken resolves the call on the instance and reaches
    the C++ slot anyway, which blocks. The guard therefore installs a Python
    subclass and rebinds the name in the modules that imported it.
    """
    assert headless_dialogs.menu_class is not None, "no headless QMenu installed"
    menu = headless_dialogs.menu_class()
    menu.addAction("noop")
    assert menu.exec() is None
    assert menu.popup(None) is None
    assert headless_dialogs.called("QMenu.exec")


def test_production_modules_see_the_non_blocking_menu(headless_dialogs, qapp):
    """Rebinding only helps if it reached the modules that build menus."""
    import importlib
    import sys

    # A module that imports QMenu *after* the fixture ran must still be covered:
    # the guard rebinds the name in PySide6.QtWidgets as well as in the modules
    # that had already imported it.
    import PySide6.QtWidgets as qtwidgets

    assert qtwidgets.QMenu is headless_dialogs.menu_class

    candidates = [
        name
        for name in sys.modules
        if name.startswith(("editor", "engine"))
        and getattr(sys.modules[name], "QMenu", None) is not None
    ]
    if not candidates:
        module = importlib.import_module("editor.widgets.generic_graph_editor")
        candidates = [module.__name__] if getattr(module, "QMenu", None) else []
    if candidates:
        for name in candidates:
            assert sys.modules[name].QMenu is headless_dialogs.menu_class, (
                f"{name} still holds Qt's QMenu; a menu it builds would block"
            )


def test_patching_qmenu_exec_directly_would_not_have_worked(qapp):
    """Pins the reason the guard is shaped the way it is.

    If a future PySide6 makes plain setattr work, this test fails and the
    subclass machinery can be simplified away -- that is the point of pinning it.
    """
    assert type(QMenu.exec).__name__ == "builtin_function_or_method", (
        "QMenu.exec is no longer a Shiboken built-in; re-check whether the "
        "subclass rebinding is still necessary"
    )


def test_application_exec_raises_instead_of_blocking(qapp):
    """QApplication.exec never returns until quit(); answering it would be a lie."""
    with pytest.raises(AssertionError, match="QApplication.exec"):
        QApplication.exec()


def test_calls_are_recorded_for_assertions(headless_dialogs, qapp):
    QFileDialog.getSaveFileName(None, "Save", "", "*.zscene")
    QMessageBox.question(None, "t", "m")
    assert headless_dialogs.call_names[-2:] == ["getSaveFileName", "QMessageBox.question"]


@pytest.mark.real_dialog
def test_real_dialog_opt_out_restores_the_genuine_api(qapp):
    """A test whose subject IS the dialog API must not be locked out.

    NOTHING MODAL MAY BE CALLED HERE. An earlier draft of this test called
    ``QMessageBox.question`` to show the guard was gone; with the guard gone
    that opens a real modal, and the run hung exactly the way the seam exists to
    prevent. The proof has to be made by inspection instead: the attributes are
    Qt's built-ins again rather than the guard's Python replacements.
    """
    for function in (
        QFileDialog.getSaveFileName,
        QFileDialog.getOpenFileName,
        QFileDialog.getExistingDirectory,
        QMessageBox.question,
        QMessageBox.warning,
    ):
        assert type(function).__name__ == "builtin_function_or_method", (
            f"{function} is still the headless replacement; the opt-out did not apply"
        )
    assert QDialog.exec is not None and "function" not in type(QDialog.exec).__name__


def test_opt_out_is_scoped_to_the_marked_test(headless_dialogs, qapp):
    """The test right after an opted-out one is guarded again."""
    path, _ = QFileDialog.getSaveFileName(None, "Save", "", "*.zscene")
    assert path == headless_dialogs.save_path
