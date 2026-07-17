from __future__ import annotations

from engine.core.component import Component
from engine.game_object import GameObject
from engine.ui.runtime_components import ButtonComponent, Canvas, ImageComponent, LabelComponent


class GameplayMarker(Component):
    component_type = "GameplayMarker"


def test_pure_ui_owner_is_hidden_from_world_draw():
    obj = GameObject("UI Owner")
    component = ButtonComponent()
    obj.add_component(component)

    component.on_runtime_start()

    assert getattr(obj, "runtime_hidden", False) is True
    assert obj.active is True


def test_mixed_gameplay_owner_stays_visible_with_ui_component():
    player = GameObject("Player")
    player.add_component(GameplayMarker())
    component = ButtonComponent()
    player.add_component(component)

    component.on_runtime_start()

    assert getattr(player, "runtime_hidden", False) is False
    assert player.active is True


def test_all_pure_ui_components_are_hidden_from_world_draw():
    for component in (Canvas(), LabelComponent(), ImageComponent(), ButtonComponent()):
        obj = GameObject("UI Owner")
        obj.add_component(component)

        component.on_runtime_start()

        assert getattr(obj, "runtime_hidden", False) is True
        assert obj.active is True
