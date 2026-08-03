from types import SimpleNamespace

from editor.visual_scripting.mini_live_viewport import ViewportMode
from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock


class _Signal:
    def __init__(self) -> None:
        self.calls = 0

    def emit(self) -> None:
        self.calls += 1


class _Button:
    def __init__(self) -> None:
        self.enabled = None

    def setEnabled(self, enabled) -> None:
        self.enabled = bool(enabled)


class _Timer:
    def __init__(self) -> None:
        self.interval = None
        self.stopped = False

    def start(self, interval) -> None:
        self.interval = interval
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


def test_visual_logic_transport_emits_only_official_commands() -> None:
    play_calls = []
    stop_signal = _Signal()
    commands = []
    dock = SimpleNamespace(
        graph_editor=SimpleNamespace(
            request_play=lambda: play_calls.append("play"),
            stop_requested=stop_signal,
        ),
        _dispatch=commands.append,
    )

    VisualScriptingEditorDock._play(dock)
    VisualScriptingEditorDock._pause(dock)
    VisualScriptingEditorDock._stop(dock)

    assert play_calls == ["play"]
    assert commands == ["pause"]
    assert stop_signal.calls == 1


def test_visual_logic_mini_viewport_mirrors_confirmed_runtime_state() -> None:
    modes = []
    timer = _Timer()
    dock = SimpleNamespace(
        mini_viewport=SimpleNamespace(set_viewport_mode=modes.append),
        btn_play=_Button(),
        btn_pause=_Button(),
        btn_stop=_Button(),
        _sync_timer=timer,
        sync_from_host=lambda: None,
    )

    VisualScriptingEditorDock.set_play_state(dock, "play")
    assert modes[-1] == ViewportMode.GAME
    assert timer.interval == 33
    assert dock.btn_play.enabled is False
    assert dock.btn_pause.enabled is True
    assert dock.btn_stop.enabled is True

    VisualScriptingEditorDock.set_play_state(dock, "pause")
    assert modes[-1] == ViewportMode.DEBUG
    assert dock.btn_play.enabled is True

    VisualScriptingEditorDock.set_play_state(dock, "edit")
    assert modes[-1] == ViewportMode.EDITOR
    assert timer.stopped is True
    assert dock.btn_pause.enabled is False
    assert dock.btn_stop.enabled is False
