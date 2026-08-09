import json

from PySide6.QtWidgets import QApplication

from editor.ui_builder.ui_builder_dock import UIBuilderDock
from engine.ui.runtime import UICanvas, UIButton, UIContainer, UIImage, UILabel, widget_from_dict


def _app():
    return QApplication.instance() or QApplication([])


def test_runtime_ui_round_trip_preserves_properties_and_hierarchy():
    root = UIContainer("Root", "Horizontal")
    button = UIButton("Play")
    button.text = "Jogar"
    button.x = 120
    root.add_child(button)
    rebuilt = widget_from_dict(root.serialize())
    assert isinstance(rebuilt, UIContainer)
    assert rebuilt.layout_mode == "Horizontal"
    assert isinstance(rebuilt.children[0], UIButton)
    assert rebuilt.children[0].text == "Jogar"
    assert rebuilt.children[0].parent is rebuilt


def test_runtime_ui_accepts_canonical_canvas_alias():
    rebuilt = widget_from_dict({
        "name": "MainCanvas",
        "type": "canvas",
        "children": [{"name": "PlayButton", "type": "Button", "text": "Play"}],
    })

    assert isinstance(rebuilt, UICanvas)
    assert isinstance(rebuilt.children[0], UIButton)
    assert rebuilt.children[0].text == "Play"


def test_builder_add_edit_duplicate_delete_and_persist(tmp_path):
    _app()
    dock = UIBuilderDock(project_root=tmp_path)
    container = UIContainer("Menu")
    dock.add_widget(container)
    assert dock.inspector_tabs.tabText(1) == "Ajuda"
    assert "Container" in dock.help_browser.toPlainText()
    dock.select_widget(container)
    label = UILabel("Title")
    dock.add_widget(label)
    assert label.parent is container

    dock.select_widget(label)
    dock.txt_name.setText("GameTitle")
    dock.txt_text.setText("Zennity")
    dock.spin_x.setValue(90)
    dock.apply_inspector()
    assert label.name == "GameTitle"
    assert label.text == "Zennity"
    assert label.x == 90

    dock.duplicate_selected()
    assert len(container.children) == 2
    dock.delete_selected()
    assert len(container.children) == 1

    path = tmp_path / "Assets" / "UI" / "Main.zui"
    dock.current_path = path
    assert dock.save()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["format"] == "zennity.ui"

    restored = UIBuilderDock(project_root=tmp_path)
    assert restored.load_document(path)
    assert restored.preview_canvas.canvas_runtime.children[0].children[0].text == "Zennity"


def test_ui_image_uses_project_asset_picker(tmp_path, monkeypatch):
    _app()
    dock = UIBuilderDock(project_root=tmp_path)
    image = UIImage("Logo")
    dock.add_widget(image)

    class _Picker:
        selected_path = "Assets/Images/logo.png"

        def __init__(self, project_root, kind, parent):
            assert project_root == tmp_path.resolve()
            assert kind == "image"

        def exec(self):
            return True

    monkeypatch.setattr(
        "editor.ui_builder.ui_builder_dock.LogicAssetPickerDialog", _Picker
    )
    dock.choose_image_asset()

    assert dock.txt_asset.isReadOnly()
    assert image.texture_path == "Assets/Images/logo.png"
