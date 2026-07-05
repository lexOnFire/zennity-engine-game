from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from editor_legacy.editor_2d import Editor2DScene
from engine.components.script_component import ScriptComponent
from engine.core.component_registry import component_registry
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.prefabs.prefab_loader import create_prefab_from_object, instantiate_prefab
from engine.runtime import Input, RuntimeManager
from engine.scene import deserialize_scene, load_scene, save_scene


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add_to_scene(scene: Editor2DScene, obj: GameObject) -> None:
    scene._add_go(obj)
    scene.editable_objects.append(obj)


def _write_beta_script(script_path: Path, events_path: Path) -> None:
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        "\n".join(
            [
                "from engine.runtime import Input, ScriptBehaviour",
                f"EVENTS = {str(events_path)!r}",
                "",
                "def log(message):",
                "    with open(EVENTS, 'a', encoding='utf-8') as fp:",
                "        fp.write(str(message) + '\\n')",
                "",
                "class BetaPlayer(ScriptBehaviour):",
                "    def on_start(self):",
                "        log(f'start:{self.game_object.name}')",
                "",
                "    def on_update(self, delta_time):",
                "        if Input.is_key_pressed('Space'):",
                "            log('space_pressed')",
                "        if Input.is_key_down('Space'):",
                "            self.transform.position[0] += 25.0 * delta_time",
                "        if Input.is_mouse_pressed('left'):",
                "            log(f'mouse:{Input.mouse_position()}')",
                "",
                "    def on_destroy(self):",
                "        log('destroy')",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_events(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def test_beta_complete_project_flow_keeps_editor_world_intact(tmp_path: Path) -> None:
    project_root = tmp_path / "GettingStarted"
    script_path = project_root / "Assets" / "Scripts" / "beta_player.py"
    events_path = tmp_path / "events.txt"
    _write_beta_script(script_path, events_path)

    editor_scene = _empty_editor_scene()
    editor_scene.name = "BetaSandbox"

    player = GameObject("Player", tag="Player")
    player.layer = 1
    player.mesh_type = "Retângulo"
    player.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    player.transform.scale = np.array([32.0, 32.0, 1.0], dtype=np.float32)
    player.add_component(RigidBody(use_gravity=False, is_kinematic=True))
    player.add_component(BoxCollider(width=32.0, height=32.0, is_trigger=True))
    player.add_component(ScriptComponent(str(script_path)))
    _add_to_scene(editor_scene, player)
    editor_scene.selected_index = 0

    scene_path = project_root / "Assets" / "Scenes" / "BetaSandbox.zscene"
    saved_scene_path = save_scene(editor_scene, scene_path)
    loaded_scene_data = load_scene(saved_scene_path)
    assert loaded_scene_data["scene_name"] == "BetaSandbox"
    assert loaded_scene_data["objects"][0].get_component(ScriptComponent).script_path == str(script_path)

    prefab_path = project_root / "Assets" / "Prefabs" / "Player.zprefab"
    prefab_uuid = create_prefab_from_object(player, prefab_path)
    prefab_instance = instantiate_prefab(prefab_path)
    assert prefab_instance.prefab_uuid == prefab_uuid
    assert prefab_instance.get_component(BoxCollider) is not None
    assert prefab_instance.get_component(ScriptComponent).script_path == str(script_path)

    manager = RuntimeManager()
    runtime_scene = manager.start_play(editor_scene)
    runtime_player = runtime_scene.runtime_for_editor(player)
    original_editor_x = float(player.transform.position[0])

    manager.input.key_down("Space")
    manager.input.set_mouse_position(100.0, 200.0)
    manager.input.mouse_down("left")
    manager.tick(0.5)

    assert Input.is_key_down("Space") is True
    assert float(runtime_player.transform.position[0]) == 22.5
    assert float(player.transform.position[0]) == original_editor_x

    manager.input.key_up("Space")
    manager.input.mouse_up("left")
    manager.tick(0.1)
    manager.stop_play()

    assert manager.runtime_scene is None
    assert Input.is_key_down("Space") is False
    assert float(player.transform.position[0]) == original_editor_x
    assert _read_events(events_path) == [
        "start:Player",
        "space_pressed",
        "mouse:(100.0, 200.0)",
        "destroy",
    ]


def test_beta_old_scene_and_prefab_formats_remain_compatible() -> None:
    old_scene = {
        "scene_name": "LegacyScene",
        "engine_version": "0.1.0",
        "objects": [
            {
                "id": "legacy-player",
                "name": "LegacyPlayer",
                "tag": "Player",
                "transform": {
                    "position": [1, 2, 0],
                    "rotation": [0, 0, 0],
                    "scale": [16, 16, 1],
                },
                "components": {
                    "collider": {"type": "box", "width": 16, "height": 16},
                    "rigidbody": {"mass": 2, "use_gravity": False},
                    "scripts": ["Assets/Scripts/legacy_player.py"],
                },
            }
        ],
    }

    data = deserialize_scene(old_scene)
    obj = data["objects"][0]

    assert obj.name == "LegacyPlayer"
    assert obj.get_component(BoxCollider) is not None
    assert obj.get_component(RigidBody).mass == 2
    assert obj.get_component(ScriptComponent).script_path == "Assets/Scripts/legacy_player.py"
    assert component_registry.resolve("Script") is ScriptComponent

    old_prefab = {
        "prefab_uuid": "legacy-prefab",
        "source_object_name": "LegacyPrefab",
        "transform": {"position": [3, 4, 0], "scale": [8, 8, 1]},
        "components": {
            "rigidbody": {"mass": 1, "use_gravity": False},
            "scripts": ["Assets/Scripts/prefab.py"],
        },
    }
    prefab_path_data = json.loads(json.dumps(old_prefab))
    prefab_obj = instantiate_prefab_from_data(prefab_path_data)

    assert prefab_obj.name == "LegacyPrefab"
    assert prefab_obj.prefab_uuid == "legacy-prefab"
    assert prefab_obj.get_component(RigidBody) is not None
    assert prefab_obj.get_component(ScriptComponent).script_path == "Assets/Scripts/prefab.py"


def test_getting_started_example_scene_is_loadable() -> None:
    scene_path = Path("examples/GettingStarted/Assets/Scenes/GettingStarted.zscene")
    script_path = Path("examples/GettingStarted/Assets/Scripts/player_controller.py")

    assert scene_path.exists()
    assert script_path.exists()

    data = load_scene(scene_path)
    obj = data["objects"][0]
    script = obj.get_component(ScriptComponent)

    assert data["scene_name"] == "GettingStarted"
    assert obj.name == "Player"
    assert obj.get_component(BoxCollider) is not None
    assert obj.get_component(RigidBody) is not None
    assert script is not None
    assert Path(script.script_path).as_posix() == script_path.as_posix()


def instantiate_prefab_from_data(data: dict) -> GameObject:
    from engine.prefabs.prefab_serializer import deserialize_prefab

    return deserialize_prefab(data)
