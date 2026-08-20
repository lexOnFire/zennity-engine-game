"""Top-level Qt widgets must not survive the module that created them.

PHASE 13 item 13.1-A.

``QApplication`` is a process-wide singleton, and a ``QWidget`` with no parent is
kept alive by Qt itself -- it appears in ``QApplication.topLevelWidgets()`` until
something destroys it.  Python dropping the last reference is not enough.  So a
test that builds an editor window and simply returns leaks that whole widget tree
into every test that runs after it.

Measured on this suite at d864de05, after ``tests/editor`` alone:

    6744 top-level widgets / 100080 widgets live in one QApplication

Nothing complains about that directly.  What it breaks is anything whose cost is
proportional to the number of live widgets, and the sharpest example is a global
stylesheet: ``QApplication.setStyleSheet`` re-polishes every widget in the
application.  ``ThemeManager.apply_theme`` does exactly that, so
``tests/unit/test_sprint5_ux_theme_polishing.py`` -- two lines, ~instant on its
own -- ran for more than five minutes and the suite appeared to hang.  It was
never that test's fault, and it moved around as the suite grew, which is why it
looked non-deterministic.

The cleanup is per *module*, not per test: within a module, widgets built in one
test are routinely reused by the next, and tearing them down between tests would
change what the suite means.  Across modules there is no such contract -- a test
that depends on a widget another file left behind is already order-dependent.
"""

from __future__ import annotations

import pytest


def _qt_application():
    """The live QApplication, or None when Qt was never imported."""
    try:
        from PySide6.QtWidgets import QApplication
    except Exception:  # pragma: no cover - Qt is optional for pure-engine runs
        return None
    return QApplication.instance()


def _top_level_widgets(app) -> list:
    try:
        return list(app.topLevelWidgets())
    except RuntimeError:  # pragma: no cover - application already torn down
        return []


@pytest.fixture(autouse=True, scope="module")
def _qt_widget_lifetime():
    """Destroy top-level widgets a module created, once it is done.

    Widgets already alive on entry are left alone: they belong to whatever
    created them earlier, and this fixture only cleans up after its own module.
    """
    app = _qt_application()
    pre_existing = set(_top_level_widgets(app)) if app is not None else set()

    yield

    app = _qt_application()
    if app is None:
        return

    for widget in _top_level_widgets(app):
        if widget in pre_existing:
            continue
        try:
            widget.close()
            widget.setParent(None)
            widget.deleteLater()
        except RuntimeError:
            # Already destroyed on the C++ side; nothing left to release.
            continue

    _drain_deferred_deletes(app)


def _drain_deferred_deletes(app) -> None:
    """Actually run the deletions ``deleteLater`` only scheduled.

    ``processEvents`` alone does not do it: Qt holds ``DeferredDelete`` events
    back until the event loop that posted them unwinds, and under pytest there
    is no ``exec()`` to unwind. ``sendPostedEvents(None, DeferredDelete)``
    delivers them regardless of loop level, which is the difference between
    widgets that are scheduled for deletion and widgets that are gone.
    """
    try:
        from PySide6.QtCore import QCoreApplication, QEvent
    except Exception:  # pragma: no cover
        return
    try:
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        app.processEvents()
    except RuntimeError:  # pragma: no cover
        pass
