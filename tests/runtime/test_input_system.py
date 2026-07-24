from __future__ import annotations

from pathlib import Path

import numpy as np

from editor_legacy.editor_2d import Editor2DScene
from engine.components.script_component import ScriptComponent
from engine.game_object import GameObject
from engine.input import Input
from engine.runtime import InputManager, RuntimeManager


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
    obj.transform.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    obj.add_component(ScriptComponent(str(script_path)))
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def _write_input_script(path: Path, events_path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "from engine.runtime import Input, ScriptBehaviour",
                f"EVENTS = {str(events_path)!r}",
                "",
                "def log(message):",
                "    with open(EVENTS, 'a', encoding='utf-8') as fp:",
                "        fp.write(str(message) + '\\n')",
                "",
                "class InputProbe(ScriptBehaviour):",
                "    def on_update(self, delta_time):",
                "        log(",
                "            f\"space_down={Input.is_key_down('Space')}|\"",
                "            f\"space_pressed={Input.is_key_pressed('Space')}|\"",
                "            f\"space_released={Input.is_key_released('Space')}|\"",
                "            f\"mouse_down={Input.is_mouse_down('left')}|\"",
                "            f\"mouse_pressed={Input.is_mouse_pressed('left')}|\"",
                "            f\"mouse_released={Input.is_mouse_released('left')}|\"",
                "            f\"pos={Input.mouse_position()}|\"",
                "            f\"delta={Input.mouse_delta()}\"",
                "        )",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_events(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def test_key_pressed_down_and_released_states_last_one_frame() -> None:
    manager = InputManager()
    manager.start()

    manager.key_down("Space")
    manager.update()
    assert manager.is_key_pressed("space") is True
    assert manager.is_key_down("Space") is True
    assert manager.is_key_released("Space") is False

    manager.update()
    assert manager.is_key_pressed("Space") is False
    assert manager.is_key_down("Space") is True

    manager.key_up("Space")
    manager.update()
    assert manager.is_key_released("Space") is True
    assert manager.is_key_down("Space") is False

    manager.update()
    assert manager.is_key_released("Space") is False


def test_mouse_pressed_down_released_position_and_delta() -> None:
    manager = InputManager()
    manager.start()

    manager.set_mouse_position(10, 20)
    manager.mouse_down("left")
    manager.update()

    assert manager.is_mouse_pressed(1) is True
    assert manager.is_mouse_down("left") is True
    assert manager.mouse_position() == (10.0, 20.0)
    assert manager.mouse_delta() == (10.0, 20.0)

    manager.set_mouse_position(15, 18)
    manager.update()

    assert manager.is_mouse_pressed(1) is False
    assert manager.is_mouse_down(1) is True
    assert manager.mouse_delta() == (5.0, -2.0)

    manager.mouse_up(1)
    manager.update()

    assert manager.is_mouse_released("left") is True
    assert manager.is_mouse_down("left") is False


def test_multiple_keys_can_be_held_simultaneously() -> None:
    manager = InputManager()
    manager.start()

    manager.key_down("A")
    manager.key_down("D")
    manager.update()

    assert manager.is_key_down("a") is True
    assert manager.is_key_down("d") is True
    assert manager.is_key_pressed("a") is True
    assert manager.is_key_pressed("d") is True


def test_input_api_is_inactive_outside_play() -> None:
    Input.unbind_manager()

    assert Input.is_key_down("Space") is False
    assert Input.is_key_pressed("Space") is False
    assert Input.is_key_released("Space") is False
    assert Input.is_mouse_down("left") is False
    assert Input.mouse_position() == (0.0, 0.0)
    assert Input.mouse_delta() == (0.0, 0.0)


def test_runtime_manager_updates_input_before_scripts(tmp_path: Path) -> None:
    events = tmp_path / "events.txt"
    script = tmp_path / "input_probe.py"
    _write_input_script(script, events)
    scene = _empty_editor_scene()
    _add_script_object(scene, "Player", script)
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.input.key_down("Space")
    manager.input.set_mouse_position(10, 20)
    manager.input.mouse_down("left")
    manager.tick(0.1)

    assert _read_events(events) == [
        "space_down=True|space_pressed=True|space_released=False|"
        "mouse_down=True|mouse_pressed=True|mouse_released=False|"
        "pos=(10.0, 20.0)|delta=(10.0, 20.0)"
    ]

    manager.tick(0.1)

    assert _read_events(events)[1] == (
        "space_down=True|space_pressed=False|space_released=False|"
        "mouse_down=True|mouse_pressed=False|mouse_released=False|"
        "pos=(10.0, 20.0)|delta=(0.0, 0.0)"
    )


def test_runtime_manager_clears_input_after_stop() -> None:
    scene = _empty_editor_scene()
    manager = RuntimeManager()

    manager.start_play(scene)
    manager.input.key_down("Space")
    manager.input.mouse_down("left")
    manager.tick(0.1)
    assert Input.is_key_down("Space") is True

    manager.stop_play()

    assert manager.input.is_key_down("Space") is False
    assert manager.input.is_mouse_down("left") is False
    assert Input.is_key_down("Space") is False


def test_runtime_manager_ignores_input_events_when_not_playing() -> None:
    manager = RuntimeManager()

    manager.handle_input_event(type("Event", (), {"type": "key_down", "key": "Space"})())
    manager.tick(0.1)

    assert manager.input.is_key_down("Space") is False
