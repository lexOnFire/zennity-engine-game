from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from editor.inspector import inspector_plugin_registry
from engine.animation.animator import Animator
from engine.ui.runtime_components import ImageComponent


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_image_inspector_has_sprite_selector(qapp) -> None:
    component = ImageComponent(sprite_path="Assets/Character/player.png")
    plugin = inspector_plugin_registry.plugin_for(component)

    widget = plugin.create_widget(component, None, None)

    assert widget.property("component_type") == "Image"
    assert hasattr(widget, "cb_sprite")
    assert widget.cb_sprite.currentText() == "Assets/Character/player.png"


def test_image_sprite_selector_updates_component(qapp) -> None:
    component = ImageComponent()
    plugin = inspector_plugin_registry.plugin_for(component)
    widget = plugin.create_widget(component, None, None)

    widget.cb_sprite.setCurrentText("Assets/Character/hero.png")
    widget.cb_sprite.lineEdit().editingFinished.emit()

    assert component.sprite_path == "Assets/Character/hero.png"


def test_animator_inspector_exposes_default_clip_and_speed(qapp) -> None:
    animator = Animator(speed=1.5)
    plugin = inspector_plugin_registry.plugin_for(animator)

    widget = plugin.create_widget(animator, None, None)

    assert widget.property("component_type") == "Animator"
    assert hasattr(widget, "cb_default_clip")
    assert hasattr(widget, "sb_speed")
    assert widget.sb_speed.value() == pytest.approx(1.5)


def test_animator_speed_field_updates_component(qapp) -> None:
    animator = Animator(speed=1.0)
    plugin = inspector_plugin_registry.plugin_for(animator)
    widget = plugin.create_widget(animator, None, None)

    widget.sb_speed.setValue(2.25)

    assert animator.speed == pytest.approx(2.25)
