from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from editor_legacy.editor_2d import Editor2DScene
from engine.components.script_component import ScriptComponent
from engine.core import Component
from engine.core.component_registry import register_component
from engine.game_object import GameObject
from engine.runtime import RuntimeManager, Time


class TimeProbe(Component):
    component_type = "TimeProbe"
    updates: list[float] = []

    def on_runtime_update(self, delta_time: float) -> None:
        self.updates.append(float(delta_time))


register_component(TimeProbe)


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add_probe_object(scene: Editor2DScene) -> GameObject:
    obj = GameObject("Timer")
    obj.transform.position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
    obj.add_component(TimeProbe())
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def _write_script(path: Path, events_path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "from engine.runtime import ScriptBehaviour, Time",
                f"EVENTS = {str(events_path)!r}",
                "",
                "def log(message):",
                "    with open(EVENTS, 'a', encoding='utf-8') as fp:",
                "        fp.write(str(message) + '\\n')",
                "",
                "class TimeScript(ScriptBehaviour):",
                "    def on_update(self, delta_time):",
                "        log(f'{delta_time}:{Time.delta_time}:{Time.time}:{Time.frame_count}:{Time.time_scale}')",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_events(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def setup_function() -> None:
    Time._runtime_reset()
    TimeProbe.updates.clear()


def teardown_function() -> None:
    Time._runtime_reset()
    TimeProbe.updates.clear()


def test_time_defaults_and_fixed_delta_time() -> None:
    assert Time.delta_time == pytest.approx(0.0)
    assert Time.unscaled_delta_time == pytest.approx(0.0)
    assert Time.time == pytest.approx(0.0)
    assert Time.unscaled_time == pytest.approx(0.0)
    assert Time.frame_count == 0
    assert Time.time_scale == pytest.approx(1.0)
    assert Time.fixed_delta_time == pytest.approx(1.0 / 60.0)


def test_tick_without_play_does_not_advance_time() -> None:
    manager = RuntimeManager()

    manager.tick(0.25)

    assert Time.delta_time == pytest.approx(0.0)
    assert Time.unscaled_delta_time == pytest.approx(0.0)
    assert Time.frame_count == 0


def test_runtime_tick_updates_scaled_and_unscaled_time() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.25)

    assert Time.delta_time == pytest.approx(0.25)
    assert Time.unscaled_delta_time == pytest.approx(0.25)
    assert Time.time == pytest.approx(0.25)
    assert Time.unscaled_time == pytest.approx(0.25)
    assert Time.frame_count == 1
    assert TimeProbe.updates == [pytest.approx(0.25)]


def test_multiple_ticks_accumulate_time_and_frames() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.1)
    manager.tick(0.2)

    assert Time.time == pytest.approx(0.3)
    assert Time.unscaled_time == pytest.approx(0.3)
    assert Time.frame_count == 2
    assert TimeProbe.updates == [pytest.approx(0.1), pytest.approx(0.2)]


def test_time_scale_zero_pauses_scaled_delta_but_runtime_still_ticks() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    Time.time_scale = 0.0
    manager.tick(0.25)

    assert Time.delta_time == pytest.approx(0.0)
    assert Time.unscaled_delta_time == pytest.approx(0.25)
    assert Time.time == pytest.approx(0.0)
    assert Time.unscaled_time == pytest.approx(0.25)
    assert Time.frame_count == 1
    assert TimeProbe.updates == [pytest.approx(0.0)]


def test_time_scale_above_one_speeds_scaled_time() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    Time.time_scale = 2.0
    manager.tick(0.25)

    assert Time.delta_time == pytest.approx(0.5)
    assert Time.time == pytest.approx(0.5)
    assert Time.unscaled_time == pytest.approx(0.25)
    assert TimeProbe.updates == [pytest.approx(0.5)]


def test_time_scale_below_one_slows_scaled_time() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    Time.time_scale = 0.5
    manager.tick(0.25)

    assert Time.delta_time == pytest.approx(0.125)
    assert Time.time == pytest.approx(0.125)
    assert Time.unscaled_time == pytest.approx(0.25)
    assert TimeProbe.updates == [pytest.approx(0.125)]


def test_stop_resets_runtime_time_state() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    Time.time_scale = 2.0
    manager.tick(0.25)
    manager.stop_play()

    assert Time.delta_time == pytest.approx(0.0)
    assert Time.unscaled_delta_time == pytest.approx(0.0)
    assert Time.time == pytest.approx(0.0)
    assert Time.unscaled_time == pytest.approx(0.0)
    assert Time.frame_count == 0
    assert Time.time_scale == pytest.approx(1.0)


def test_new_play_session_starts_with_clean_time_state() -> None:
    scene = _empty_editor_scene()
    _add_probe_object(scene)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.25)
    manager.stop_play()
    manager.start_play(scene)

    assert Time.delta_time == pytest.approx(0.0)
    assert Time.time == pytest.approx(0.0)
    assert Time.frame_count == 0


def test_script_behaviour_can_read_time_api(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "time_script.py"
    _write_script(script, events)
    scene = _empty_editor_scene()
    obj = GameObject("Player")
    obj.add_component(ScriptComponent(str(script)))
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    manager = RuntimeManager()

    manager.start_play(scene)
    Time.time_scale = 0.5
    manager.tick(0.2)

    assert _read_events(events) == ["0.1:0.1:0.1:1:0.5"]
