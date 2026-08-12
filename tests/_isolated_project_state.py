"""Editor state that must never land in the working repository.

PHASE 9 recovery item 9B. Stage 2.1 stopped the suite from writing *assets*
into ``Assets/``; it did not cover the editor's own state files, and those turn
out to be worse, because they are read back:

    editor/widgets/generic_graph_editor.py:554
        _graph_cache_file_path() -> Path.cwd() / ".zennity"
        _cache_last_opened_file() writes  last_graph_<category>.json
        _auto_load_last_file()   reads it on the next construction

So a test that opens a graph leaves the path behind, and the *next* test to
build a ``GenericGraphEditorWidget`` silently inherits that graph. That is
exactly how ``test_delete_removes_selected_behavior_node_and_marks_document_dirty``
failed: it asserted the canvas was empty after deleting its one node, and found
three nodes ('wait', 'move', ...) restored from a previous test's cache. It
passes in isolation and fails after the suite -- the definition of an
order-dependent test.

``AutosaveManager`` has the same shape: constructed with the editor's
``project_root``, which defaults to ``Path.cwd()``, it writes
``.zennity_autosave.json``, ``.zennity_autosave_manifest.json`` and a lockfile
into the repository root.

The rule here is narrow on purpose: state is redirected **only when it would be
written inside the repository**. Tests that already pass their own ``tmp_path``
-- ``tests/editor/test_scene_autosave_controller.py`` asserts the recovery file
lands in *its* directory -- are untouched, and so is production behaviour.

Each test gets a fresh directory, created lazily on first use. A shared one
would isolate the repository but not the tests from each other, which is half
the bug.

Opt out with ``@pytest.mark.real_project_state`` when the repository-rooted
behaviour is itself the subject.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _is_inside_repository(path: Path) -> bool:
    try:
        Path(path).resolve().relative_to(REPO_ROOT)
    except (ValueError, OSError):
        return False
    return True


class _LazyStateDir:
    """A temp directory created on first use, not on fixture setup.

    Every test in the suite gets this fixture; eagerly making ~4000 directories
    would cost more than the isolation is worth, and almost no test touches
    editor state at all.
    """

    def __init__(self) -> None:
        self._path: Path | None = None
        self._handle: tempfile.TemporaryDirectory | None = None

    def path(self) -> Path:
        if self._path is None:
            self._handle = tempfile.TemporaryDirectory(prefix="zennity-state-")
            self._path = Path(self._handle.name)
        return self._path

    def cleanup(self) -> None:
        if self._handle is not None:
            self._handle.cleanup()
            self._handle = None
            self._path = None


def pytest_configure(config):  # pragma: no cover - pytest hook
    config.addinivalue_line(
        "markers",
        "real_project_state: opt out of the project-state isolation guard; the "
        "test's subject is the repository-rooted state itself "
        "(see tests/_isolated_project_state.py)",
    )


@pytest.fixture(autouse=True)
def _isolated_project_state(request, monkeypatch):
    """Redirect editor state that would be written into the repository."""
    if request.node.get_closest_marker("real_project_state") is not None:
        yield None
        return

    state = _LazyStateDir()

    try:
        from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
    except Exception:  # pragma: no cover - Qt or editor unavailable
        GenericGraphEditorWidget = None

    if GenericGraphEditorWidget is not None:
        def _cache_path(self) -> Path:
            cache_dir = state.path() / ".zennity"
            cache_dir.mkdir(parents=True, exist_ok=True)
            slug = self.category_filter.casefold().replace(" ", "_")
            return cache_dir / f"last_graph_{slug}.json"

        monkeypatch.setattr(
            GenericGraphEditorWidget, "_graph_cache_file_path", _cache_path, raising=False
        )

    try:
        from editor.autosave_manager import AutosaveManager
    except Exception:  # pragma: no cover
        AutosaveManager = None

    if AutosaveManager is not None:
        original_init = AutosaveManager.__init__

        def _init(self, project_root, *args, **kwargs):
            # A root the test chose itself is left alone; only a root that
            # resolves into the checkout is redirected.
            if _is_inside_repository(project_root):
                project_root = state.path()
            original_init(self, project_root, *args, **kwargs)

        monkeypatch.setattr(AutosaveManager, "__init__", _init)

    # The UI Builder keeps the same kind of "last opened document" cache, under
    # ``project_root/.zennity/last_ui.json``, and creates the directory even
    # when it writes nothing -- which is why an empty ``.zennity/`` kept
    # appearing in the checkout.
    try:
        from editor.ui_builder.ui_builder_dock import UIBuilderDock
    except Exception:  # pragma: no cover - Qt or editor unavailable
        UIBuilderDock = None

    if UIBuilderDock is not None:
        def _ui_cache_path(self) -> Path:
            cache_dir = state.path() / ".zennity"
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir / "last_ui.json"

        monkeypatch.setattr(
            UIBuilderDock, "_last_ui_cache_path", _ui_cache_path, raising=False
        )

    # The Logic Graph editor's crash recovery for an *untitled* document goes to
    # ``project_root/.zennity/recovery/``. This one is written by a deferred
    # autosave timer, so it lands after the test that armed it has already torn
    # down -- it never showed up when a file was run alone, only at the end of a
    # directory run, which is what made it the last one to find.
    try:
        from editor.widgets.logic_graph.editor_mixins.persistence_mixin import (
            LogicGraphPersistenceMixin,
        )
    except Exception:  # pragma: no cover - Qt or editor unavailable
        LogicGraphPersistenceMixin = None

    if LogicGraphPersistenceMixin is not None:
        original_recovery_path = LogicGraphPersistenceMixin._recovery_path

        def _recovery_path(self, path: Path | None) -> Path:
            if path is not None:
                # Named documents recover next to themselves; that path is the
                # caller's, not the repository's.
                return original_recovery_path(self, path)
            # Swap the root and let production compute the rest, so the layout
            # and the file name stay whatever production says they are -- the
            # original creates its directory as a side effect, so it must not be
            # called with the repository root at all.
            previous_root = getattr(self, "project_root", None)
            if previous_root is None or not _is_inside_repository(previous_root):
                return original_recovery_path(self, path)
            self.project_root = state.path()
            try:
                return original_recovery_path(self, path)
            finally:
                self.project_root = previous_root

        monkeypatch.setattr(
            LogicGraphPersistenceMixin, "_recovery_path", _recovery_path, raising=False
        )

    yield state
    state.cleanup()
