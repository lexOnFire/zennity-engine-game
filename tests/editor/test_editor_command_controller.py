from __future__ import annotations

from queue import SimpleQueue
from types import SimpleNamespace

from editor.editor_command_controller import EditorCommandController


class _Status:
    def __init__(self) -> None:
        self.messages = []

    def showMessage(self, message: str) -> None:
        self.messages.append(message)


def _host():
    status = _Status()
    host = SimpleNamespace(
        _play_controller=SimpleNamespace(blocks=lambda command: False),
        _commands=SimpleQueue(), _selected_name=None, history=0,
    )
    host.statusBar = lambda: status
    host._record_history = lambda: setattr(host, "history", host.history + 1)
    return host, status


def test_editor_command_controller_forwards_regular_command() -> None:
    host, _ = _host()
    message = {"type": "select_object", "name": "Player"}

    EditorCommandController(host).dispatch(message)

    assert host._commands.get_nowait() == message


def test_editor_command_controller_delegates_new_scene_to_scene_objects() -> None:
    host, _ = _host()
    host.new_scene_calls = 0
    host._scene_objects = SimpleNamespace(
        new_scene=lambda: setattr(host, "new_scene_calls", host.new_scene_calls + 1)
    )

    EditorCommandController(host).dispatch({"type": "new_scene"})

    assert host.new_scene_calls == 1
    assert host._commands.empty()


def test_editor_command_controller_records_move_before_forwarding() -> None:
    host, _ = _host()
    host._selected_name = "Player"

    EditorCommandController(host).dispatch({"type": "move_selected", "dx": 3})

    assert host.history == 1
    assert host._commands.get_nowait()["type"] == "move_selected"


def test_editor_command_controller_blocks_scene_command_during_play() -> None:
    host, status = _host()
    host._play_controller = SimpleNamespace(blocks=lambda command: command == "new_scene")
    host._scene_objects = SimpleNamespace(
        new_scene=lambda: (_ for _ in ()).throw(AssertionError("must not execute"))
    )

    EditorCommandController(host).dispatch({"type": "new_scene"})

    assert host._commands.empty()
    assert status.messages == ["Pare o Play Mode antes de alterar a cena"]


def test_editor_command_controller_delegates_reset_to_scene_objects() -> None:
    host, _ = _host()
    host.reset_calls = 0
    host._scene_objects = SimpleNamespace(
        reset_to_initial=lambda: setattr(host, "reset_calls", host.reset_calls + 1)
    )

    EditorCommandController(host).dispatch({"type": "reset_from_interface"})

    assert host.reset_calls == 1
    assert host._commands.empty()


class _Action:
    def __init__(self) -> None:
        self.enabled = True

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)


class _Tabs:
    def __init__(self) -> None:
        self.index = None

    def setCurrentIndex(self, index: int) -> None:
        self.index = int(index)


def test_stop_command_enters_stopping_state_until_viewport_confirms_edit() -> None:
    host, status = _host()
    host._scene_snapshot = [{"name": "Player"}]
    host._scene_document = {}
    host._play_controller = SimpleNamespace(
        blocks=lambda _command: False,
        plan=lambda *_args, **_kwargs: SimpleNamespace(commands=({"type": "stop"},)),
    )
    host.toolbar_actions = {
        "Play": _Action(),
        "Pause": _Action(),
        "Stop": _Action(),
    }
    host.viewport_tabs = _Tabs()

    EditorCommandController(host).dispatch({"type": "stop"})

    assert host._runtime_stopping is True
    assert host.viewport_tabs.index == 0
    assert host.toolbar_actions["Play"].enabled is False
    assert host.toolbar_actions["Pause"].enabled is False
    assert host.toolbar_actions["Stop"].enabled is False
    assert status.messages[-1] == "Encerrando Play Mode..."
    assert host._commands.get_nowait() == {"type": "stop"}
