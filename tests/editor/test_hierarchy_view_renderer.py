import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTreeWidget

from editor.hierarchy_view_renderer import HierarchyViewRenderer


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def make_editor() -> SimpleNamespace:
    scene = [{"id": "player", "name": "Player", "x": 0.0}]
    return SimpleNamespace(
        hierarchy_tree=QTreeWidget(),
        _scene_document={"scene_name": "Main"},
        _scene_snapshot=scene,
        _objects_by_name={"Player": scene[0]},
        _runtime_objects_by_name={},
        _runtime_playing=False,
        _selected_name="Player",
    )


def test_hierarchy_skips_transform_only_updates(qapp: QApplication) -> None:
    editor = make_editor()
    renderer = HierarchyViewRenderer(editor)

    assert renderer.refresh() is True
    editor._scene_snapshot[0]["x"] = 500.0
    assert renderer.refresh() is False

    assert renderer.rebuild_count == 1
    assert renderer.skipped_count == 1
    assert editor.hierarchy_tree.currentItem().data(0, 0x0100) == "Player"


def test_hierarchy_rebuilds_for_structural_and_runtime_changes(qapp: QApplication) -> None:
    editor = make_editor()
    renderer = HierarchyViewRenderer(editor)
    renderer.refresh()
    editor._scene_snapshot[0]["name"] = "Hero"
    editor._objects_by_name = {"Hero": editor._scene_snapshot[0]}
    assert renderer.refresh() is True

    editor._runtime_playing = True
    editor._runtime_objects_by_name["Bullet"] = {
        "id": "bullet", "name": "Bullet", "spawned_by_logic": True,
    }
    assert renderer.refresh() is True
    assert "Runtime (1)" in editor.hierarchy_tree.topLevelItem(0).child(1).text(0)


def test_official_editor_delegates_hierarchy_rendering() -> None:
    source = (
        open("editor/isolated_editor_main.py", encoding="utf-8").read()
        + open("editor/hierarchy_controller.py", encoding="utf-8").read()
    )

    assert "self.renderer.refresh(force=force)" in source
    assert "self.hierarchy_tree.clear()" not in source


def test_hierarchy_displays_and_tracks_transform_lock(qapp: QApplication) -> None:
    editor = make_editor()
    renderer = HierarchyViewRenderer(editor)
    renderer.refresh()

    editor._scene_snapshot[0]["editor_locked"] = True

    assert renderer.refresh() is True
    item = editor.hierarchy_tree.topLevelItem(0).child(0)
    assert item.text(0).startswith("🔒 ")
    assert "bloqueada" in item.toolTip(0)
