import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from types import SimpleNamespace
from PySide6.QtWidgets import QApplication
from editor.premium_inspector_panel import RealInspectorPanel


def _app():
    return QApplication.instance() or QApplication([])


def test_inspector_tag_combo_is_editable_and_supports_custom_tags() -> None:
    _app()
    panel = RealInspectorPanel()
    assert panel.object_tag.isEditable() is True

    dummy_obj = SimpleNamespace(
        name="Apple",
        active=True,
        is_static=False,
        tag="Untagged",
        layer="Default",
    )

    panel.load_object(dummy_obj)
    assert panel.object_tag.currentText() == "Untagged"

    # Set custom tag "Food"
    panel.object_tag.setCurrentText("Food")
    assert dummy_obj.tag == "Food"
    assert panel.object_tag.findText("Food") != -1

    # Load object with pre-existing custom tag "Comida"
    food_obj = SimpleNamespace(
        name="Meat",
        active=True,
        is_static=False,
        tag="Comida",
        layer="Default",
    )
    panel.load_object(food_obj)
    assert panel.object_tag.currentText() == "Comida"
    assert panel.object_tag.findText("Comida") != -1


def test_object_switching_preserves_individual_tags() -> None:
    _app()
    panel = RealInspectorPanel()

    obj_food = SimpleNamespace(name="FoodObj", active=True, is_static=False, tag="Food", layer="Default")
    obj_enemy = SimpleNamespace(name="EnemyObj", active=True, is_static=False, tag="Enemy", layer="Default")

    # Load food object
    panel.load_object(obj_food)
    assert panel.object_tag.currentText() == "Food"
    assert obj_food.tag == "Food"

    # Switch to enemy object
    panel.load_object(obj_enemy)
    assert panel.object_tag.currentText() == "Enemy"
    assert obj_enemy.tag == "Enemy"
    assert obj_food.tag == "Food"  # Ensure Food object wasn't overwritten!

    # Switch back to food object
    panel.load_object(obj_food)
    assert panel.object_tag.currentText() == "Food"
    assert obj_food.tag == "Food"
    assert obj_enemy.tag == "Enemy"

