from pathlib import Path
from types import SimpleNamespace

from editor.controllers.selection_controller import EditorSelectionController
from editor.inspector_controller import InspectorComponentController


class ValueField:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value

    def isChecked(self):
        return bool(self._value)


class Queue:
    def __init__(self) -> None:
        self.messages = []

    def put(self, message) -> None:
        self.messages.append(message)


def _host(obj: dict) -> SimpleNamespace:
    host = SimpleNamespace(
        _selected_name="Player",
        _updating_inspector=False,
        _objects_by_name={"Player": obj},
        _scene_snapshot=[obj],
        _record_history=lambda: None,
        _update_inspector=lambda _name: None,
        _scene_controller=SimpleNamespace(publish_snapshot=lambda _snapshot: None),
        _commands=Queue(),
        physics_fields={"use_gravity": ValueField(False), "is_kinematic": ValueField(True)},
        collider_fields={
            "width": ValueField(32), "height": ValueField(48),
            "radius": ValueField(16), "offset_x": ValueField(2), "offset_y": ValueField(3),
        },
        collider_trigger_field=ValueField(True),
    )
    host._selection = EditorSelectionController(host)
    return host


def test_physics_controller_mutates_model_and_sends_runtime_command() -> None:
    obj = {"rigidbody": {"use_gravity": True, "is_kinematic": False}}
    host = _host(obj)

    InspectorComponentController(host).send_physics()

    assert obj["rigidbody"] == {"use_gravity": False, "is_kinematic": True}
    assert host._commands.messages[-1]["type"] == "set_physics"


def test_collider_controller_uses_shape_specific_fields() -> None:
    obj = {"collider": {"type": "circle"}}
    host = _host(obj)

    InspectorComponentController(host).send_collider()

    assert obj["collider"] == {
        "type": "circle", "radius": 16.0, "offset_x": 2.0,
        "offset_y": 3.0, "is_trigger": True,
    }
    assert host._commands.messages[-1]["collider"] is not obj["collider"]


def test_camera_toggle_keeps_component_name_in_sync() -> None:
    obj = {"component_names": []}
    host = _host(obj)
    controller = InspectorComponentController(host)

    controller.toggle_camera(True)
    assert "Camera2D" in obj["component_names"]
    assert "camera" in obj

    controller.toggle_camera(False)
    assert "Camera2D" not in obj["component_names"]
    assert "camera" not in obj


def test_audio_discovery_returns_only_supported_project_assets(tmp_path: Path) -> None:
    audio = tmp_path / "Assets" / "Audio"
    audio.mkdir(parents=True)
    (audio / "theme.ogg").write_bytes(b"ogg")
    (audio / "voice.WAV").write_bytes(b"wav")
    (audio / "notes.txt").write_text("ignore", encoding="utf-8")

    assert InspectorComponentController.available_audio_files(tmp_path) == [
        "Assets/Audio/theme.ogg", "Assets/Audio/voice.WAV",
    ]


def test_ui_visibility_mutation_is_published() -> None:
    obj = {"ui": {"type": "label", "visible": True}}
    host = _host(obj)
    published = []
    host._scene_controller.publish_snapshot = lambda snapshot: published.append(snapshot)

    InspectorComponentController(host).toggle_ui_visibility(False)

    assert obj["ui"]["visible"] is False
    assert published == [[obj]]


def test_ensure_canvas_is_idempotent() -> None:
    host = _host({})
    host._unique_name = lambda base: base
    host._log = lambda _level, _message: None
    controller = InspectorComponentController(host)

    controller.ensure_canvas()
    controller.ensure_canvas()

    canvases = [obj for obj in host._scene_snapshot if obj.get("ui", {}).get("type") == "canvas"]
    assert len(canvases) == 1
    assert host._objects_by_name["Canvas"] is canvases[0]
