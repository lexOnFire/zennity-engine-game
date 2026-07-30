from __future__ import annotations

from queue import SimpleQueue
from types import SimpleNamespace

from editor.scene_object_controller import SceneObjectController


class _SceneBridge:
    def __init__(self) -> None:
        self.snapshots = 0
        self.selected = []

    def publish_snapshot(self, _snapshot) -> None:
        self.snapshots += 1

    def select(self, name: str) -> None:
        self.selected.append(name)


def _host():
    obj = {"id": "original", "name": "Player", "x": 1.0, "y": 2.0}
    host = SimpleNamespace(
        _scene_snapshot=[obj], _objects_by_name={"Player": obj}, _selected_name="Player",
        _play_session=SimpleNamespace(is_running=False), _scene_controller=_SceneBridge(),
        _commands=SimpleQueue(), history=0, inspected=[],
        _scene_document={"objects": [obj]}, _current_scene_path="Old.zscene",
        _runtime_objects_by_name={"Ghost": {}}, _runtime_animator_states={"Player": {}},
        _drag_history_snapshot=[obj], autosave_scheduled=0,
    )
    host._scene_history = SimpleNamespace(clear=lambda: setattr(host, "history", 0))
    host._autosave = SimpleNamespace(
        schedule=lambda: setattr(host, "autosave_scheduled", host.autosave_scheduled + 1)
    )
    host.logic_workspace = SimpleNamespace(clear_runtime_trace=lambda: None)
    host._record_history = lambda: setattr(host, "history", host.history + 1)
    host._refresh_hierarchy = lambda: None
    host._update_inspector = lambda name: host.inspected.append(name)
    host._clear_inspector_view = lambda: None
    host.statusBar = lambda: SimpleNamespace(showMessage=lambda _message: None)
    host._log = lambda *_args: None
    return host


def test_new_scene_is_fully_clean_and_detached_from_previous_project() -> None:
    host = _host()

    SceneObjectController(host).new_scene()

    assert host._scene_snapshot == []
    assert host._objects_by_name == {}
    assert host._runtime_objects_by_name == {}
    assert host._runtime_animator_states == {}
    assert host._selected_name is None
    assert host._current_scene_path is None
    assert host._scene_document["objects"] == []
    assert host._scene_document["blackboard"] == {"variables": {}}
    assert host._scene_controller.snapshots == 1
    assert host.autosave_scheduled == 1


def test_empty_object_has_no_renderer_physics_collision_or_logic() -> None:
    host = _host()

    SceneObjectController(host).create("Empty")

    created = host._scene_snapshot[-1]
    assert created["mesh_type"] is None
    assert created["renderer_enabled"] is False
    assert "rigidbody" not in created
    assert "collider" not in created
    assert "logic" not in created


def test_scene_object_controller_generates_stable_unique_names() -> None:
    host = _host()
    host._objects_by_name["Player_2"] = {}
    controller = SceneObjectController(host)

    assert controller.unique_name("Enemy") == "Enemy"
    assert controller.unique_name("Player") == "Player_3"


def test_scene_object_controller_duplicates_with_new_identity() -> None:
    host = _host()

    SceneObjectController(host).duplicate_selected()

    duplicate = host._scene_snapshot[-1]
    assert duplicate["name"] == "Player_copy"
    assert duplicate["id"] != "original"
    assert (duplicate["x"], duplicate["y"]) == (17.0, 18.0)
    assert host.history == 1
    assert host._scene_controller.selected == ["Player_copy"]


def test_scene_object_controller_blocks_mutation_during_play() -> None:
    host = _host()
    host._play_session.is_running = True
    controller = SceneObjectController(host)

    controller.create("Enemy")
    controller.duplicate_selected()
    controller.delete("Player")

    assert len(host._scene_snapshot) == 1
    assert host.history == 0


def test_scene_object_controller_deletes_unselected_object() -> None:
    host = _host()
    host._selected_name = None

    SceneObjectController(host).delete("Player")

    assert host._scene_snapshot == []
    assert host._objects_by_name == {}
    assert host._scene_controller.snapshots == 1


def test_scene_object_controller_resets_to_initial_scene() -> None:
    host = _host()
    initial = {"id": "initial", "name": "Player", "x": 100.0, "y": 200.0}
    host._initial_scene_snapshot = [initial]
    host._scene_snapshot[0]["x"] = 500.0

    SceneObjectController(host).reset_to_initial()

    assert host.history == 1
    assert host._scene_snapshot == [initial]
    assert host._scene_snapshot[0] is not initial
    assert host._objects_by_name == {"Player": host._scene_snapshot[0]}
    assert host._scene_controller.snapshots == 1
    assert host.inspected == ["Player"]
