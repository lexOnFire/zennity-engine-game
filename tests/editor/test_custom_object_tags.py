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
