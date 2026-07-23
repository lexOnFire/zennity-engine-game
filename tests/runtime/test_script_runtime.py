from __future__ import annotations

from pathlib import Path

import numpy as np

from editor_legacy.editor_2d import Editor2DScene
from engine.components.script_component import ScriptComponent
from engine.game_object import GameObject
from engine.runtime import RuntimeManager, RuntimeState


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add_script_object(scene: Editor2DScene, name: str, script_path: Path) -> GameObject:
    obj = GameObject(name)
    obj.transform.position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
    obj.add_component(ScriptComponent(str(script_path)))
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def _write_script(path: Path, events_path: Path, body: str) -> None:
    path.write_text(
        "\n".join(
            [
                "from engine.runtime import ScriptBehaviour",
                f"EVENTS = {str(events_path)!r}",
                "",
                "def log(message):",
                "    with open(EVENTS, 'a', encoding='utf-8') as fp:",
                "        fp.write(str(message) + '\\n')",
                "",
                body,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_events(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def test_script_runtime_loads_script_and_binds_runtime_context(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "player_script.py"
    _write_script(
        script,
        events,
        """
class PlayerBehaviour(ScriptBehaviour):
    def on_start(self):
        log(f"start:{self.game_object.name}:{self.transform is self.game_object.transform}:{self.scene is not None}:{self.runtime is not None}")
""",
    )
    scene = _empty_editor_scene()
    editor_obj = _add_script_object(scene, "Player", script)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)
    instances = list(runtime_scene.script_runtime.instances.values())

    assert len(instances) == 1
    assert instances[0].behaviour.game_object is runtime_obj
    assert _read_events(events) == ["start:Player:True:True:True"]


def test_script_lifecycle_awake_start_update_destroy(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "lifecycle_script.py"
    _write_script(
        script,
        events,
        """
class Script(ScriptBehaviour):
    def on_awake(self):
        log("awake")

    def on_start(self):
        log("start")

    def on_update(self, delta_time):
        log(f"update:{delta_time}")

    def on_destroy(self):
        log("destroy")
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.tick(0.25)
    manager.stop_play()

    assert _read_events(events) == ["awake", "start", "update:0.25", "destroy"]


def test_multiple_game_objects_get_separate_script_instances(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "shared_script.py"
    _write_script(
        script,
        events,
        """
class SharedBehaviour(ScriptBehaviour):
    def on_start(self):
        log(f"start:{self.game_object.name}:{id(self)}")
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "PlayerA", script)
    _add_script_object(scene, "PlayerB", script)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    behaviour_ids = {id(instance.behaviour) for instance in runtime_scene.script_runtime.instances.values()}
    lines = _read_events(events)

    assert len(runtime_scene.script_runtime.instances) == 2
    assert len(behaviour_ids) == 2
    assert any(line.startswith("start:PlayerA:") for line in lines)
    assert any(line.startswith("start:PlayerB:") for line in lines)


def test_script_update_error_disables_only_failed_component(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    bad_script = tmp_path / "bad_script.py"
    good_script = tmp_path / "good_script.py"
    _write_script(
        bad_script,
        events,
        """
class BadBehaviour(ScriptBehaviour):
    def on_update(self, delta_time):
        log("bad:update")
        raise RuntimeError("boom")

    def on_destroy(self):
        log("bad:destroy")
""",
    )
    _write_script(
        good_script,
        events,
        """
class GoodBehaviour(ScriptBehaviour):
    def on_update(self, delta_time):
        log("good:update")

    def on_destroy(self):
        log("good:destroy")
""",
    )
    scene = _empty_editor_scene()
    bad_editor_obj = _add_script_object(scene, "Bad", bad_script)
    good_editor_obj = _add_script_object(scene, "Good", good_script)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    manager.tick(0.1)
    bad_runtime_obj = runtime_scene.runtime_for_editor(bad_editor_obj)
    good_runtime_obj = runtime_scene.runtime_for_editor(good_editor_obj)
    bad_component = bad_runtime_obj.get_component(ScriptComponent)
    good_component = good_runtime_obj.get_component(ScriptComponent)

    assert manager.state == RuntimeState.PLAYING
    assert bad_component.enabled is False
    assert good_component.enabled is True
    assert len(runtime_scene.script_runtime.errors) == 1
    assert "boom" in runtime_scene.script_runtime.errors[0]

    manager.tick(0.1)
    manager.stop_play()

    assert _read_events(events) == [
        "bad:update",
        "good:update",
        "good:update",
        "good:destroy",
        "bad:destroy",
    ]


def test_script_instances_are_cleared_on_stop(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "cleanup_script.py"
    _write_script(
        script,
        events,
        """
class CleanupBehaviour(ScriptBehaviour):
    pass
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    assert len(runtime_scene.script_runtime.instances) == 1

    manager.stop_play()

    assert runtime_scene.script_runtime.instances == {}
    assert manager.runtime_scene is None
    assert manager.state == RuntimeState.STOPPED


def test_scripts_do_not_execute_outside_play(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "outside_play_script.py"
    _write_script(
        script,
        events,
        """
class OutsidePlayBehaviour(ScriptBehaviour):
    def on_update(self, delta_time):
        log("update")
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()

    manager.tick(0.1)

    assert _read_events(events) == []
    assert manager.runtime_scene is None


def test_scripts_modify_only_runtime_world(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "isolation_script.py"
    _write_script(
        script,
        events,
        """
class IsolationBehaviour(ScriptBehaviour):
    def on_start(self):
        self.transform.position[0] = 77.0
        log(f"runtime:{self.transform.position[0]}")
""",
    )
    scene = _empty_editor_scene()
    editor_obj = _add_script_object(scene, "Player", script)
    original_x = float(editor_obj.transform.position[0])
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)

    assert float(runtime_obj.transform.position[0]) == 77.0
    assert float(editor_obj.transform.position[0]) == original_x
    assert _read_events(events) == ["runtime:77.0"]


def test_hot_reload_preserves_behaviour_and_scene_state(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "reloadable.py"
    _write_script(
        script,
        events,
        """
class Reloadable(ScriptBehaviour):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def on_update(self, delta_time):
        self.counter += 1
        self.transform.position[0] = 25.0
""",
    )
    scene = _empty_editor_scene()
    editor_obj = _add_script_object(scene, "Player", script)
    manager = RuntimeManager()
    runtime_scene = manager.start_play(scene)
    manager.tick(0.1)

    _write_script(
        script,
        events,
        """
class Reloadable(ScriptBehaviour):
    def __init__(self):
        super().__init__()
        self.counter = 100

    def on_reload(self, previous_state):
        log(f"reload:{previous_state['counter']}")

    def on_update(self, delta_time):
        self.counter += 10
""",
    )
    manager.tick(0.1)
    instance = next(iter(runtime_scene.script_runtime.instances.values()))
    runtime_obj = runtime_scene.runtime_for_editor(editor_obj)

    assert instance.behaviour.counter == 11
    assert float(runtime_obj.transform.position[0]) == 25.0
    assert _read_events(events) == ["reload:1"]


def test_failed_hot_reload_keeps_previous_script_until_source_is_fixed(
    tmp_path: Path,
) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "recoverable.py"
    _write_script(
        script,
        events,
        """
class Recoverable(ScriptBehaviour):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def on_update(self, delta_time):
        self.counter += 1
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()
    runtime_scene = manager.start_play(scene)
    manager.tick(0.1)
    component, instance = next(iter(runtime_scene.script_runtime.instances.items()))

    script.write_text("class Broken(:\n", encoding="utf-8")
    manager.tick(0.1)
    manager.tick(0.1)

    assert component.enabled is True
    assert instance.behaviour.counter == 3
    assert len(runtime_scene.script_runtime.errors) == 1
    assert ":reload:" in runtime_scene.script_runtime.errors[0]

    _write_script(
        script,
        events,
        """
class Recovered(ScriptBehaviour):
    def on_update(self, delta_time):
        self.counter += 5
""",
    )
    manager.tick(0.1)

    assert instance.behaviour.counter == 8
    assert component.enabled is True


def test_missing_script_reports_once_and_recovers_when_restored(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "temporary.py"
    _write_script(
        script,
        events,
        """
class Temporary(ScriptBehaviour):
    def __init__(self):
        super().__init__()
        self.updates = 0

    def on_update(self, delta_time):
        self.updates += 1
""",
    )
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()
    runtime_scene = manager.start_play(scene)
    manager.tick(0.1)
    instance = next(iter(runtime_scene.script_runtime.instances.values()))

    script.unlink()
    manager.tick(0.1)
    manager.tick(0.1)

    assert instance.behaviour.updates == 3
    assert len(runtime_scene.script_runtime.errors) == 1

    _write_script(
        script,
        events,
        """
class Temporary(ScriptBehaviour):
    def on_update(self, delta_time):
        self.updates += 4
""",
    )
    manager.tick(0.1)

    assert instance.behaviour.updates == 7
