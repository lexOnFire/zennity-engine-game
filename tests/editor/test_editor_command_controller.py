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


def test_editor_command_controller_records_move_before_forwarding() -> None:
    host, _ = _host()
    host._selected_name = "Player"

    EditorCommandController(host).dispatch({"type": "move_selected", "dx": 3})

    assert host.history == 1
    assert host._commands.get_nowait()["type"] == "move_selected"


def test_editor_command_controller_blocks_scene_command_during_play() -> None:
    host, status = _host()
    host._play_controller = SimpleNamespace(blocks=lambda command: command == "new_scene")
    host._new_scene = lambda: (_ for _ in ()).throw(AssertionError("must not execute"))

    EditorCommandController(host).dispatch({"type": "new_scene"})

    assert host._commands.empty()
    assert status.messages == ["Pare o Play Mode antes de alterar a cena"]
