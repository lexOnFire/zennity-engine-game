"""Signal lifecycle contracts for editor controllers."""

from __future__ import annotations

from types import SimpleNamespace

from editor.asset_browser_controller import AssetBrowserController
from editor.console_controller import ConsoleController


class FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)

    def disconnect(self, callback: object) -> None:
        self.callbacks.remove(callback)


class FakeCheck:
    def __init__(self) -> None:
        self.toggled = FakeSignal()


def test_asset_browser_connect_disconnect_is_idempotent(tmp_path) -> None:
    tree = SimpleNamespace(itemClicked=FakeSignal(), itemDoubleClicked=FakeSignal())
    controller = AssetBrowserController(SimpleNamespace(assets_tree=tree), tmp_path)
    assert controller.connect() is True
    assert controller.connect() is False
    assert len(tree.itemClicked.callbacks) == len(tree.itemDoubleClicked.callbacks) == 1
    assert controller.disconnect() is True
    assert controller.disconnect() is False
    assert tree.itemClicked.callbacks == tree.itemDoubleClicked.callbacks == []


def test_console_connect_disconnect_is_idempotent() -> None:
    checks = {"INFO": FakeCheck(), "ERROR": FakeCheck()}
    clear_button = SimpleNamespace(clicked=FakeSignal())
    controller = ConsoleController(SimpleNamespace(
        console_level_checks=checks, console_clear_button=clear_button,
    ))
    assert controller.connect() is True
    assert controller.connect() is False
    assert all(len(check.toggled.callbacks) == 1 for check in checks.values())
    assert len(clear_button.clicked.callbacks) == 1
    assert controller.disconnect() is True
    assert controller.disconnect() is False
    assert all(check.toggled.callbacks == [] for check in checks.values())
    assert clear_button.clicked.callbacks == []
