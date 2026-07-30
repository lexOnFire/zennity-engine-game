from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from editor.widgets.logic_asset_picker import ASSET_KINDS, LogicAssetPickerDialog
from editor.widgets.logic_graph_editor import LogicGraphEditor
from engine.logic.graph_asset import create_logic_node


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_asset_picker_uses_type_tabs_and_project_relative_paths(tmp_path: Path) -> None:
    _app()
    image = tmp_path / "Assets" / "Textures" / "player.png"
    audio = tmp_path / "Assets" / "Audio" / "jump.wav"
    image.parent.mkdir(parents=True)
    audio.parent.mkdir(parents=True)
    image.write_bytes(b"png")
    audio.write_bytes(b"wav")

    picker = LogicAssetPickerDialog(tmp_path, "image")

    assert picker.tabs.count() == len(ASSET_KINDS)
    assert picker.tabs.tabText(picker.tabs.currentIndex()) == "Imagem"
    assert picker.tree.topLevelItemCount() == 1
    assert picker.tree.topLevelItem(0).data(0, Qt.UserRole) == (
        "Assets/Textures/player.png"
    )
    assert sum(
        picker.tabs.isTabEnabled(index)
        for index in range(picker.tabs.count())
    ) == 1


def test_asset_picker_searches_only_compatible_asset_list(tmp_path: Path) -> None:
    _app()
    directory = tmp_path / "Assets" / "Audio"
    directory.mkdir(parents=True)
    (directory / "jump.wav").write_bytes(b"wav")
    (directory / "theme.ogg").write_bytes(b"ogg")

    picker = LogicAssetPickerDialog(tmp_path, "audio")
    picker.search.setText("theme")

    assert picker.tree.topLevelItemCount() == 1
    assert picker.tree.topLevelItem(0).text(0) == "theme.ogg"


def test_graph_asset_paths_are_selected_from_library_not_typed(tmp_path: Path) -> None:
    app = _app()
    editor = LogicGraphEditor(project_root=tmp_path)
    node = create_logic_node("add_audio_source")
    editor.set_graph({**editor.graph, "nodes": [node], "edges": []})
    editor.node_items[node["id"]].setSelected(True)
    app.processEvents()
    path_item = next(
        editor.property_tree.topLevelItem(index)
        for index in range(editor.property_tree.topLevelItemCount())
        if editor.property_tree.topLevelItem(index).data(0, Qt.UserRole) == "path"
    )

    assert not bool(path_item.flags() & Qt.ItemIsEditable)
    assert editor.property_asset_button.text() == "Escolher Áudio..."
