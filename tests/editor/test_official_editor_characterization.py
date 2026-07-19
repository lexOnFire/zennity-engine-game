"""Caracterização mínima do shell oficial; roda quando Qt headless está disponível."""
from __future__ import annotations

from queue import Queue

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets", exc_type=ImportError)

from editor.isolated_editor_main import IsolatedEditorWindow


@pytest.fixture(scope="module")
def app():
    instance = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield instance


def test_official_editor_boots_and_preserves_document_invariants(app):
    window = IsolatedEditorWindow(None, Queue(), Queue())
    try:
        original_count = len(window._scene_snapshot)
        window._create_object("Player")
        assert len(window._scene_snapshot) == original_count + 1
        created = window._scene_snapshot[-1]
        assert created["id"]
        assert window._objects_by_name[created["name"]] is created
        window._delete_object(created["name"])
        assert len(window._scene_snapshot) == original_count
    finally:
        window.close()


def test_official_editor_play_session_restores_edit_state(app):
    window = IsolatedEditorWindow(None, Queue(), Queue())
    try:
        original = window._play_session.begin(window._scene_snapshot, "Player")
        runtime = [dict(item, x=999) for item in original]
        window._play_session.finish()
        restored, selected = window._play_session.consume_scene_snapshot(runtime)
        assert restored == original
        assert selected == "Player"
    finally:
        window.close()
