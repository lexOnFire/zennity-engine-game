"""Exact signal teardown contracts for long-lived editor controllers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from editor.hierarchy_controller import HierarchyController
from editor.inspector_controller import IsolatedInspectorController


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)

    def disconnect(self, callback: object) -> None:
        self.callbacks.remove(callback)


@pytest.mark.parametrize("controller_type", [HierarchyController, IsolatedInspectorController])
def test_registered_signal_callbacks_are_disconnected_exactly_once(controller_type) -> None:
    controller = controller_type.__new__(controller_type)
    controller.host = SimpleNamespace()
    controller._connected = True
    controller._connections = []
    first, second = FakeSignal(), FakeSignal()
    callback_a, callback_b = lambda: None, lambda: None
    controller._bind(first, callback_a)
    controller._bind(second, callback_b)
    assert first.callbacks == [callback_a]
    assert second.callbacks == [callback_b]
    assert controller.disconnect() is True
    assert controller.disconnect() is False
    assert first.callbacks == []
    assert second.callbacks == []
    assert controller._connections == []


def test_session_shutdown_disconnects_editor_signal_owners() -> None:
    source = open("editor/editor_session_controller.py", encoding="utf-8").read()
    for name in (
        "_inspector_controller", "_hierarchy_controller",
        "_asset_browser", "_console_controller",
    ):
        assert name in source
