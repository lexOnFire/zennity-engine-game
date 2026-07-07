from __future__ import annotations

from engine.game_object import GameObject
from engine.ui.runtime_components import ButtonComponent, Canvas, ImageComponent, LabelComponent


def test_ui_runtime_start_does_not_hide_owner_game_object():
    player = GameObject("Player")
    component = ButtonComponent()
    player.add_component(component)

    component.on_runtime_start()

    assert not hasattr(player, "runtime_hidden")
    assert player.active is True


def test_all_ui_components_leave_owner_visible_on_runtime_start():
    for component in (Canvas(), LabelComponent(), ImageComponent(), ButtonComponent()):
        obj = GameObject("UI Owner")
        obj.add_component(component)

        component.on_runtime_start()

        assert not hasattr(obj, "runtime_hidden")
        assert obj.active is True
