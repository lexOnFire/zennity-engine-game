from __future__ import annotations

import pygame

from editor_legacy.editor_2d import Editor2DScene
from engine.game_object import GameObject
from engine.runtime import RuntimeManager
from engine.scene.scene_serializer import deserialize_game_object, serialize_game_object
from engine.ui.runtime_components import ButtonComponent, Canvas, ImageComponent, LabelComponent
from engine.ui.ui_renderer import UIRenderer


def _empty_editor_scene() -> Editor2DScene:
    scene = Editor2DScene()
    scene.start()
    for obj in list(scene.editable_objects):
        scene._remove_go(obj)
    scene.editable_objects.clear()
    scene.selected_index = -1
    return scene


def _add(scene: Editor2DScene, obj: GameObject) -> GameObject:
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    return obj


def test_canvas_component_creation() -> None:
    canvas = Canvas(visible=True, z_order=2)

    assert canvas.type_name == "Canvas"
    assert canvas.visible is True
    assert canvas.z_order == 2


def test_label_and_button_component_creation() -> None:
    label = LabelComponent(text="HP", x=8, y=12, font_size=18)
    button = ButtonComponent(text="Start", x=20, y=30)

    assert label.text == "HP"
    assert label.x == 8
    assert button.text == "Start"
    assert button.interactable is True


def test_ui_renderer_draws_label_after_canvas_exists() -> None:
    scene = _empty_editor_scene()
    _add(scene, GameObject("HUD")).add_component(Canvas())
    _add(scene, GameObject("ScoreText")).add_component(LabelComponent(text="Score", x=4, y=4))
    renderer = UIRenderer()
    surface = pygame.Surface((220, 80), pygame.SRCALPHA)

    before = pygame.image.tostring(surface, "RGBA")
    renderer.render(scene, surface)
    after = pygame.image.tostring(surface, "RGBA")

    assert after != before


def test_ui_renderer_draws_image_placeholder_and_button() -> None:
    scene = _empty_editor_scene()
    _add(scene, GameObject("HUD")).add_component(Canvas())
    _add(scene, GameObject("Icon")).add_component(ImageComponent(x=0, y=0, width=20, height=20, color=(255, 0, 0)))
    _add(scene, GameObject("Button")).add_component(ButtonComponent(text="Play", x=24, y=0, width=80, height=28))
    renderer = UIRenderer()
    surface = pygame.Surface((160, 60), pygame.SRCALPHA)

    renderer.render(scene, surface)

    assert surface.get_at((4, 4))[3] > 0
    assert surface.get_at((30, 8))[3] > 0


def test_ui_components_serialize_and_deserialize() -> None:
    obj = GameObject("Title")
    obj.add_component(LabelComponent(text="Hello", x=10, y=20, font_size=24))

    data = serialize_game_object(obj)
    restored = deserialize_game_object(data)
    label = restored.get_component(LabelComponent)

    assert data["components"]["items"][0]["type"] == "Label"
    assert label is not None
    assert label.text == "Hello"
    assert label.x == 10
    assert label.font_size == 24


def test_runtime_ui_is_isolated_and_hidden_from_world_draw() -> None:
    scene = _empty_editor_scene()
    canvas_go = _add(scene, GameObject("HUD"))
    canvas_go.add_component(Canvas())
    label_go = _add(scene, GameObject("RuntimeLabel"))
    label_go.add_component(LabelComponent(text="Runtime", x=2, y=2))
    manager = RuntimeManager()

    runtime_scene = manager.start_play(scene)
    runtime_label = runtime_scene.runtime_for_editor(label_go)

    assert runtime_label is not label_go
    assert getattr(runtime_label, "runtime_hidden", False) is True
    assert not getattr(label_go, "runtime_hidden", False)

    manager.stop_play()
