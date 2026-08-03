"""Regressões para falhas toleradas em caminhos críticos do editor."""
from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from editor.autosave_manager import AutosaveManager
from editor.runtime.command_manager import CommandManager, FunctionCommand
from editor.runtime.reactive_editor_bridge import (
    ReactiveEditorBridge,
    _patch_hierarchy_selection,
)
from editor.runtime.selection_manager import SelectionService


class _Context:
    def __init__(self) -> None:
        self.selection = SelectionService()


def test_command_listener_failure_is_logged_and_does_not_stop_following_listener(caplog):
    manager = CommandManager()
    called = []
    manager.on_after_execute.extend(
        [MagicMock(side_effect=RuntimeError("listener")), lambda _cmd: called.append(True)]
    )

    with caplog.at_level(logging.DEBUG, logger="editor.runtime.command_manager"):
        manager.execute(FunctionCommand("test", lambda: None, lambda: None))

    assert called == [True]
    assert "listener falhou" in caplog.text


def test_event_subscription_failure_is_logged_without_breaking_bridge(caplog):
    with patch("editor.core.event_bus.EventBus.subscribe", side_effect=RuntimeError("bus")), \
         caplog.at_level(logging.DEBUG, logger="editor.runtime.reactive_editor_bridge"):
        bridge = ReactiveEditorBridge(_Context())

    assert bridge is not None
    assert "assinar eventos" in caplog.text


def test_hierarchy_sync_failure_is_logged_and_absorbed(caplog):
    bridge = ReactiveEditorBridge(_Context())
    bridge._hierarchy = MagicMock()
    bridge._hierarchy.select_object_in_tree.side_effect = RuntimeError("hierarchy")

    with caplog.at_level(logging.DEBUG, logger="editor.runtime.reactive_editor_bridge"):
        bridge._sync_hierarchy(object())

    assert "sincronizar a Hierarchy" in caplog.text


def test_inspector_sync_failure_is_logged_and_absorbed(caplog):
    bridge = ReactiveEditorBridge(_Context())
    bridge._inspector = MagicMock()
    bridge._inspector.load_object.side_effect = RuntimeError("inspector")

    with caplog.at_level(logging.DEBUG, logger="editor.runtime.reactive_editor_bridge"):
        bridge._sync_inspector(object())

    assert "sincronizar o Inspector" in caplog.text


def test_hierarchy_patch_install_failure_is_logged_and_absorbed(caplog):
    hierarchy = MagicMock()
    hierarchy.on_item_selection_changed = MagicMock()
    hierarchy.tree.itemSelectionChanged.disconnect.side_effect = RuntimeError("signal")

    with caplog.at_level(logging.DEBUG, logger="editor.runtime.reactive_editor_bridge"):
        _patch_hierarchy_selection(hierarchy, SelectionService())

    assert "instalar o handler reativo" in caplog.text


def test_autosave_timer_stop_failure_is_logged_and_shutdown_continues(tmp_path, caplog):
    manager = AutosaveManager(tmp_path, lambda: {"scene": "test"})
    manager.start()
    manager._qt_timer = MagicMock()
    manager._qt_timer.stop.side_effect = RuntimeError("timer")

    with caplog.at_level(logging.DEBUG, logger="editor.autosave_manager"):
        manager.stop()

    assert manager._running is False
    assert not manager._lock_path.exists()
    assert "interromper o QTimer" in caplog.text
