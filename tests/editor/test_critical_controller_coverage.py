"""Behavioral coverage for the critical asset and hierarchy boundaries."""

from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QTreeWidgetItem

from editor.asset_browser_controller import AssetBrowserController
from editor.hierarchy_controller import HierarchyController


class FakeTree:
    def __init__(self) -> None:
        self.roots = []
        self.cleared = False
        self.selected = []

    def clear(self) -> None:
        self.cleared = True
        self.roots.clear()

    def addTopLevelItem(self, item) -> None:
        self.roots.append(item)

    def selectedItems(self):
        return self.selected


class FakeLabel:
    def __init__(self) -> None:
        self.text = ""
        self.pixmap = None
        self.state = None

    def clear(self) -> None:
        self.text = ""

    def setText(self, value) -> None:
        self.text = value

    def setPixmap(self, value) -> None:
        self.pixmap = value

    def width(self) -> int:
        return 320

    def height(self) -> int:
        return 180

    def setProperty(self, _name, value) -> None:
        self.state = value

    def style(self):
        return SimpleNamespace(unpolish=lambda _widget: None, polish=lambda _widget: None)


def test_asset_root_casing_hidden_files_and_icons(tmp_path) -> None:
    controller = AssetBrowserController(SimpleNamespace(), tmp_path)
    assert controller.asset_root() == tmp_path / "Assets"

    fallback = tmp_path / "assets"
    fallback.mkdir()
    assert controller.asset_root() == fallback
    preferred = tmp_path / "Assets"
    preferred.mkdir()
    assert controller.asset_root() == preferred

    hidden_script = preferred / "player.py"
    hidden_script.write_text("", encoding="utf-8")
    hidden_directory = preferred / "Scripts"
    hidden_directory.mkdir()
    visible_image = preferred / "hero.PNG"
    visible_image.write_bytes(b"")
    assert controller._hidden(hidden_script)
    assert controller._hidden(hidden_directory)
    assert not controller._hidden(visible_image)
    assert controller.asset_icon(preferred) == "📁 "
    assert controller.asset_icon(visible_image) == "🖼️ "
    assert controller.asset_icon(preferred / "sound.ogg") == "🔊 "
    assert controller.asset_icon(preferred / "walk.zanim") == "🎞 "
    assert controller.asset_icon(preferred / "state.zanimator") == "◉ "
    assert controller.asset_icon(preferred / "graph.zlogic") == "◇ "
    assert controller.asset_icon(preferred / "notes.txt") == "📄 "


def test_asset_refresh_drag_preview_and_logic_open(tmp_path) -> None:
    assets = tmp_path / "Assets"
    nested = assets / "Textures"
    nested.mkdir(parents=True)
    image = nested / "hero.png"
    image.write_bytes(b"image")
    (assets / "ignored.py").write_text("", encoding="utf-8")

    tree = FakeTree()
    label = FakeLabel()
    details = FakeLabel()
    opened = []
    preview_result = SimpleNamespace(pixmap=None, label="hero", details="PNG")
    preview_service = SimpleNamespace(preview=lambda path: preview_result)
    host = SimpleNamespace(
        assets_tree=tree,
        preview_label=label,
        preview_details_label=details,
        _show_logic_window=lambda **kwargs: opened.append(kwargs["preferred_path"]),
    )
    controller = AssetBrowserController(host, tmp_path, preview_service)
    controller.refresh()
    assert tree.cleared
    assert len(tree.roots) == 1
    assert tree.roots[0].isExpanded()
    assert tree.roots[0].childCount() == 1

    assert controller.dragged_path() is None
    item = QTreeWidgetItem(["hero"])
    item.setToolTip(0, str(image))
    tree.selected = [item]
    assert controller.dragged_path() == image
    controller.preview(item)
    assert label.state == "content"
    assert label.text == "hero"
    assert details.text == "PNG"

    empty = QTreeWidgetItem(["empty"])
    controller.preview(empty)
    logic = assets / "graph.zlogic"
    logic.write_text("{}", encoding="utf-8")
    logic_item = QTreeWidgetItem(["logic"])
    logic_item.setToolTip(0, str(logic))
    controller.open_item(logic_item)
    assert opened == [logic]
    controller.open_item(item)
    assert opened == [logic]


class FakeRenderer:
    def __init__(self) -> None:
        self.refresh_calls = []
        self.names = {}

    def refresh(self, *, force=False):
        self.refresh_calls.append(force)
        return force

    def item_name(self, item):
        return self.names.get(item, "")


def test_hierarchy_selection_actions_and_refresh() -> None:
    item = object()
    renderer = FakeRenderer()
    renderer.names[item] = "Player"
    selected = []
    inspected = []
    status = []
    duplicated = []
    prefabs = []
    host = SimpleNamespace(
        _objects_by_name={"Player": {}},
        _runtime_objects_by_name={},
        _runtime_playing=False,
        _scene_controller=SimpleNamespace(select=selected.append),
        _update_inspector=inspected.append,
        statusBar=lambda: SimpleNamespace(showMessage=status.append),
        _scene_objects=SimpleNamespace(duplicate_selected=lambda: duplicated.append(True)),
        _prefab_workspace=SimpleNamespace(save_selected=lambda: prefabs.append(True)),
        _selected_name=None,
    )
    controller = HierarchyController(host, renderer)
    controller.select_item(item)
    assert selected == ["Player"]
    assert inspected == ["Player"]
    assert host._selected_name == "Player"
    assert status == ["Interface: Player selecionado"]

    controller.select_and_duplicate("Player")
    controller.select_and_save_prefab("Player")
    assert duplicated == [True]
    assert prefabs == [True]
    assert controller.refresh(force=True) is True
    assert renderer.refresh_calls == [True]
    assert controller.item_name(item) == "Player"


def test_hierarchy_ignores_unknown_and_labels_runtime_selection() -> None:
    scene_item, runtime_item = object(), object()
    renderer = FakeRenderer()
    renderer.names = {scene_item: "Missing", runtime_item: "Enemy"}
    selected = []
    status = []
    host = SimpleNamespace(
        _objects_by_name={},
        _runtime_objects_by_name={"Enemy": {}},
        _runtime_playing=True,
        _scene_controller=SimpleNamespace(select=selected.append),
        _update_inspector=lambda _name: None,
        statusBar=lambda: SimpleNamespace(showMessage=status.append),
        _selected_name=None,
    )
    controller = HierarchyController(host, renderer)
    controller.select_item(scene_item)
    assert selected == []
    controller.select_item(runtime_item)
    assert selected == ["Enemy"]
    assert status == ["Runtime: Enemy selecionado"]
