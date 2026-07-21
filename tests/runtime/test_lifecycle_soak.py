"""Deterministic soak tests for editor/runtime lifecycle boundaries."""

from __future__ import annotations

import gc
import weakref
from pathlib import Path

from editor.runtime.play_session import EditorPlaySession
from editor.runtime.viewport_process_controller import ViewportProcessController
from engine.runtime.script_runtime import ScriptRuntime


class FakeQueue:
    def __init__(self) -> None:
        self.values: list[dict] = []

    def put_nowait(self, value: dict) -> None:
        self.values.append(value)


class FakeProcess:
    def __init__(self) -> None:
        self.alive = True
        self.joins = 0
        self.terminations = 0

    def is_alive(self) -> bool:
        return self.alive

    def join(self, timeout=None) -> None:
        self.joins += 1

    def terminate(self) -> None:
        self.terminations += 1
        self.alive = False


def test_play_stop_soak_releases_edit_snapshot_every_cycle() -> None:
    session = EditorPlaySession()
    original = [{"id": "player", "name": "Player", "x": 1.0}]
    for cycle in range(250):
        runtime = session.begin(original, "Player")
        runtime[0]["x"] = float(cycle)
        session.set_runtime_state("play")
        restored, selected = session.finish()
        final, selected_after = session.consume_scene_snapshot(runtime)
        assert restored == final == original
        assert selected == selected_after == "Player"
        assert session.state == "edit"
        assert session._edit_objects is None
        assert session._restore_pending is False


def test_hot_reload_loader_does_not_retain_previous_modules(tmp_path: Path) -> None:
    runtime = ScriptRuntime(object(), project_root=tmp_path)
    script = tmp_path / "reloadable.py"
    old_modules: list[weakref.ReferenceType] = []
    for version in range(100):
        script.write_text(f"VERSION = {version}\n", encoding="utf-8")
        module = runtime._load_module(script)
        assert module.VERSION == version
        if version < 99:
            old_modules.append(weakref.ref(module))
    module = None
    gc.collect()
    assert all(reference() is None for reference in old_modules)
    assert runtime.instances == {}


def test_viewport_close_soak_sends_one_shutdown_and_releases_each_process() -> None:
    queue = FakeQueue()
    controller = ViewportProcessController.from_queues(queue, FakeQueue())
    processes: list[FakeProcess] = []
    for _ in range(100):
        process = FakeProcess()
        processes.append(process)
        controller.attach(process)
        controller.shutdown(graceful_timeout=0.0, kill_timeout=0.0)
        controller.shutdown(graceful_timeout=0.0, kill_timeout=0.0)
        assert process.alive is False
        assert process.terminations == 1
    assert len(queue.values) == 100
    assert [value["type"] for value in queue.values] == ["shutdown"] * 100
    assert [value["_seq"] for value in queue.values] == list(range(1, 101))
    assert all(process.joins == 2 for process in processes)
