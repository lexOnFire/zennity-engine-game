from types import SimpleNamespace

from PySide6.QtCore import QEvent, Qt

from editor.runtime.editor_event_router import EditorEventRouter


class Commands:
    def __init__(self) -> None:
        self.values: list[dict] = []

    def put(self, value: dict) -> None:
        self.values.append(value)


class Event:
    def __init__(self, event_type, key, *, repeat: bool = False) -> None:
        self._type = event_type
        self._key = key
        self._repeat = repeat
        self.accepted = False

    def type(self):
        return self._type

    def key(self):
        return self._key

    def isAutoRepeat(self) -> bool:
        return self._repeat

    def accept(self) -> None:
        self.accepted = True


def test_runtime_input_uses_static_key_map_and_sends_only_state_changes() -> None:
    commands = Commands()
    messages: list[str] = []
    editor = SimpleNamespace(
        _runtime_playing=True,
        _runtime_keys={key: False for key in ("left", "right", "up", "down", "jump", "restart")},
        _commands=commands,
        statusBar=lambda: SimpleNamespace(showMessage=messages.append),
    )
    router = EditorEventRouter(editor)

    assert router.handle(None, Event(QEvent.KeyPress, Qt.Key_A)) is True
    assert router.handle(None, Event(QEvent.KeyPress, Qt.Key_A, repeat=True)) is True

    assert commands.values == [{
        "type": "runtime_input",
        "keys": {"left": True, "right": False, "up": False, "down": False, "jump": False, "restart": False},
    }]
    assert messages == ["Play Input: left ON"]
    assert "KEY_MAP" not in router.__dict__


def test_runtime_input_is_released_when_editor_focus_changes() -> None:
    commands = Commands()
    editor = SimpleNamespace(
        _runtime_playing=True,
        _runtime_keys={"left": True, "right": False},
        _commands=commands,
        statusBar=lambda: SimpleNamespace(showMessage=lambda _message: None),
    )
    router = EditorEventRouter(editor)

    assert router._runtime_input(SimpleNamespace(type=lambda: QEvent.FocusOut)) is None
    assert editor._runtime_keys == {"left": False, "right": False}
    assert commands.values[-1] == {
        "type": "runtime_input", "keys": {"left": False, "right": False},
    }


def test_editor_event_filter_only_delegates_and_falls_back() -> None:
    source = open("editor/isolated_editor_main.py", encoding="utf-8").read()
    block = source[source.index("    def eventFilter"):source.index("    def _flush_viewport_resize")]

    assert "self._session_controller.handle_event(watched, event)" in block
    assert "key_map =" not in block
    assert len(block.splitlines()) <= 7
