"""Play/Stop must survive a repeated stop, a level change, and a bad frame.

Three defects the existing Play/Stop suite does not reach. Each is a different
kind of hole: one in an object that is only safe by accident, one that loses the
user's work, one that disables gameplay in silence.

* ``EditorPlaySession.finish`` is not idempotent. Called twice it returns an
  empty scene, and its caller has no guard -- the editor would be left with no
  objects at all. Nothing triggers it today, but only because a toolbar and a
  viewport flag happen to block the second call.
* A ``load_scene`` during Play replaces the scene the editor restores on Stop,
  so playtesting through a level transition discards whatever was unsaved in the
  scene Play started from.
* A single exception in one frame permanently removes a graph from the running
  session, with no path back until the next Play. A transient error can stop the
  player responding for the rest of the session, leaving only a log line.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from editor.runtime.play_session import EditorPlaySession


def _scene(*names: str) -> list[dict]:
    return [{"id": str(index), "name": name} for index, name in enumerate(names, start=1)]


# ---------------------------------------------------------------------------
# Repeated stop
# ---------------------------------------------------------------------------

def _host(session: EditorPlaySession, scene: list[dict]):
    """The slice of the editor that ``play_state`` touches."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    host = MagicMock()
    host._play_session = session
    host._scene_snapshot = [dict(obj) for obj in scene]
    host._objects_by_name = {obj["name"]: obj for obj in host._scene_snapshot}
    host._selected_name = "Player"
    host._runtime_keys = {}
    host._animator_controller_dialog = None
    host._dock_visual_scripting = None
    host.toolbar_actions = {
        name: SimpleNamespace(setEnabled=lambda _value: None)
        for name in ("Play", "Pause", "Stop")
    }
    return host


def test_a_repeated_edit_event_does_not_empty_the_editor_scene() -> None:
    """A second Stop must not leave the editor with no objects.

    ``finish`` releases the edit copy once it has served -- the lifecycle soak
    requires that every cycle -- so calling it again finds nothing to restore and
    returns an empty list. The guard against that reaching the scene belongs to
    the caller, which is what this checks.
    """
    from editor.viewport_event_controller import ViewportEventController

    session = EditorPlaySession()
    scene = _scene("Player", "Camera")
    session.begin(scene, "Player")
    session.set_runtime_state("play")

    host = _host(session, scene)
    controller = ViewportEventController(host)

    controller.play_state({"state": "edit"})
    session.consume_scene_snapshot([{"id": "1", "name": "Player", "x": 999}])
    controller.play_state({"state": "edit"})

    assert [obj["name"] for obj in host._scene_snapshot] == ["Player", "Camera"], (
        "a repeated edit event emptied the editor scene"
    )
    assert set(host._objects_by_name) == {"Player", "Camera"}


def test_an_edit_event_before_any_play_leaves_the_scene_alone() -> None:
    """A stray edit event with no session must not touch the scene."""
    from editor.viewport_event_controller import ViewportEventController

    session = EditorPlaySession()
    scene = _scene("Player", "Camera")
    host = _host(session, scene)

    ViewportEventController(host).play_state({"state": "edit"})

    assert [obj["name"] for obj in host._scene_snapshot] == ["Player", "Camera"]


# ---------------------------------------------------------------------------
# Level change during Play
# ---------------------------------------------------------------------------

def test_stop_returns_to_the_scene_play_started_from() -> None:
    """Play is a sandbox: Stop restores what the user was editing."""
    session = EditorPlaySession()
    session.begin(_scene("Player", "LevelExit"), "Player")
    session.set_runtime_state("play")

    session.update_scene(_scene("Boss"))  # the game called load_scene
    restored, selected = session.finish()

    assert [obj["name"] for obj in restored] == ["Player", "LevelExit"], (
        "Stop handed back the scene the game navigated to, discarding the one "
        "the user pressed Play from along with any unsaved edits to it"
    )
    assert selected == "Player", "the selection was dropped by the level change"


def test_the_running_scene_is_still_reported_during_play() -> None:
    """Following the game is right *during* Play -- it is Stop that must not."""
    session = EditorPlaySession()
    session.begin(_scene("Player"), "Player")
    session.set_runtime_state("play")

    session.update_scene(_scene("Boss"))
    running, _selected = session.consume_scene_snapshot(_scene("Boss"))

    assert [obj["name"] for obj in running] == ["Boss"]
    assert session.state == "play"


def test_a_scene_loaded_before_play_becomes_the_restore_point() -> None:
    """Outside a session, update_scene is how the editor changes scene."""
    session = EditorPlaySession()
    session.update_scene(_scene("Boss"))

    session.begin(_scene("Boss"), "Boss")
    session.set_runtime_state("play")
    restored, _selected = session.finish()

    assert [obj["name"] for obj in restored] == ["Boss"]


# ---------------------------------------------------------------------------
# A bad frame must not disable a graph for the rest of the session
# ---------------------------------------------------------------------------

class _FlakyRuntime:
    """Raises on the frames listed, succeeds on the rest."""

    debug_paused = False

    def __init__(self, failing_frames: set[int]) -> None:
        self.failing_frames = failing_frames
        self.frame = 0
        self.updates = 0

    def update(self, _api, _dt) -> None:
        self.frame += 1
        if self.frame in self.failing_frames:
            raise RuntimeError("frame ruim")
        self.updates += 1


def _orchestrator(runtime):
    from types import SimpleNamespace
    from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator

    objects = {"Player": {"name": "Player", "active": True, "x": 0.0, "y": 0.0}}
    runtimes = {"Player": [("PlayerMovementLogic.zlogic", runtime)]}
    api = SimpleNamespace(
        begin_frame=lambda _state: None,
        drain_instructions=lambda: [],
        consume_jump=lambda: None,
    )
    bus = SimpleNamespace(dispatch=lambda: False)
    logs: list[dict] = []
    orchestrator = ViewportSessionOrchestrator(
        objects, runtimes, {}, {}, {"Player": api}, {}, lambda: bus,
        SimpleNamespace(update_lifecycle=lambda _dt: []), [],
        logs.append, lambda *a, **k: None, lambda _p: None, lambda *a: None,
    )
    orchestrator._emit_trace = lambda *a, **k: None
    orchestrator._emit_event_traces = lambda: False
    orchestrator._apply_logic_instructions = lambda _n, _o: False
    orchestrator._apply_jump = lambda *a: None
    return orchestrator, runtimes, logs


def test_a_single_bad_frame_does_not_disable_the_graph() -> None:
    """One transient error must not stop the graph running."""
    runtime = _FlakyRuntime(failing_frames={2})
    orchestrator, runtimes, _logs = _orchestrator(runtime)

    for _ in range(6):
        orchestrator.update_logic({}, 0.016, 0.0, {}, {}, False)

    assert runtimes["Player"], (
        "one bad frame removed the graph; it would stay dead for the whole session"
    )
    assert runtime.updates >= 4, "the graph stopped being updated after the error"


def test_a_persistently_failing_graph_is_still_disabled() -> None:
    """Tolerance is not the same as ignoring: a broken graph still stops."""
    runtime = _FlakyRuntime(failing_frames=set(range(1, 50)))
    orchestrator, runtimes, logs = _orchestrator(runtime)

    for _ in range(10):
        orchestrator.update_logic({}, 0.016, 0.0, {}, {}, False)

    assert not runtimes["Player"], "a graph failing every frame was never disabled"
    assert any("desligado" in str(entry.get("message", "")) for entry in logs), (
        "the graph was disabled without saying so"
    )
