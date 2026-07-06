from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from editor.phase1_editor import ZennityPhase1Editor
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def editor(qapp: QApplication):
    instance = ZennityPhase1Editor()
    _clear_scene(instance)
    yield instance
    instance.close()
    instance.deleteLater()
    qapp.processEvents()


def _clear_scene(editor: ZennityPhase1Editor) -> None:
    scene = editor._editor_scene()
    for obj in list(getattr(scene, "editable_objects", [])):
        if hasattr(scene, "_remove_go"):
            scene._remove_go(obj)
    scene.editable_objects.clear()
    editor.select_object(None)
    editor.refresh_hierarchy_from_viewport()


def _add(editor: ZennityPhase1Editor, obj: GameObject) -> GameObject:
    scene = editor._editor_scene()
    scene._add_go(obj)
    scene.editable_objects.append(obj)
    editor.refresh_hierarchy_from_viewport()
    return obj


def _item_for(editor: ZennityPhase1Editor, obj: GameObject):
    item = editor.hierarchy.find_item(obj)
    assert item is not None
    return item


def test_hierarchy_reparent_valid(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    child = _add(editor, GameObject("Child"))

    assert editor.reparent_object(child, parent)

    assert child.parent is parent
    assert child in parent.children
    assert _item_for(editor, child).parent().data(0, Qt.UserRole) is parent
    editor.undo()
    assert child.parent is None


def test_hierarchy_prevents_cycles(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    child = _add(editor, GameObject("Child"))
    editor.reparent_object(child, parent)

    assert editor.reparent_object(parent, child) is False
    assert parent.parent is None
    assert child.parent is parent


def test_hierarchy_move_to_root(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    child = _add(editor, GameObject("Child"))
    editor.reparent_object(child, parent)

    assert editor.reparent_object(child, None, 0)

    assert child.parent is None
    root = editor.hierarchy.tree.topLevelItem(0)
    assert root.child(0).data(0, Qt.UserRole) is child


def test_hierarchy_reorders_siblings(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    first = _add(editor, GameObject("First"))
    second = _add(editor, GameObject("Second"))
    editor.reparent_object(first, parent)
    editor.reparent_object(second, parent)

    assert editor.reparent_object(second, parent, 0)

    assert parent.children == [second, first]
    parent_item = _item_for(editor, parent)
    assert parent_item.child(0).data(0, Qt.UserRole) is second


def test_hierarchy_duplicate_object(editor: ZennityPhase1Editor) -> None:
    source = _add(editor, GameObject("Player"))
    source.add_component(BoxCollider(width=20, height=30))

    clone = editor.duplicate_object(source)

    assert clone is not None
    assert clone is not source
    assert clone.name == "Player_copia"
    assert clone.id != source.id
    assert clone.get_component(BoxCollider) is not None
    assert clone in editor.scene_objects()
    editor.undo()
    assert clone not in editor.scene_objects()


def test_hierarchy_duplicate_with_children(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    child = _add(editor, GameObject("Child"))
    editor.reparent_object(child, parent)

    clone = editor.duplicate_object(parent)

    assert clone is not None
    assert len(clone.children) == 1
    assert clone.children[0].name == "Child_copia"
    assert clone.children[0].id != child.id
    assert clone.children[0].parent is clone


def test_hierarchy_delete(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Parent"))
    child = _add(editor, GameObject("Child"))
    editor.reparent_object(child, parent)
    editor.select_object(parent)

    assert editor.delete_object(parent)

    assert parent not in editor.scene_objects()
    assert child not in editor.scene_objects()
    assert editor.editor_context.selection.selected is None
    editor.undo()
    assert parent in editor.scene_objects()
    assert child in editor.scene_objects()


def test_hierarchy_rename_valid(editor: ZennityPhase1Editor) -> None:
    obj = _add(editor, GameObject("OldName"))

    assert editor.rename_object(obj, "NewName")

    assert obj.name == "NewName"
    assert _item_for(editor, obj).text(0) == "NewName"
    editor.undo()
    assert obj.name == "OldName"


def test_hierarchy_rename_empty_rejected(editor: ZennityPhase1Editor) -> None:
    obj = _add(editor, GameObject("StableName"))

    assert editor.rename_object(obj, "   ") is False

    assert obj.name == "StableName"


def test_hierarchy_filter_keeps_matching_parents_visible(editor: ZennityPhase1Editor) -> None:
    parent = _add(editor, GameObject("Environment"))
    child = _add(editor, GameObject("HiddenGem"))
    editor.reparent_object(child, parent)

    editor.hierarchy.filter_tree("gem")

    parent_item = _item_for(editor, parent)
    child_item = _item_for(editor, child)
    assert parent_item.isHidden() is False
    assert child_item.isHidden() is False
    assert parent_item.isExpanded() is True

    editor.hierarchy.filter_tree("")
    assert parent_item.isHidden() is False
    assert child_item.isHidden() is False
