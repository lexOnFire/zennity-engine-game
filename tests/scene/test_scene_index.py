from engine.core.scene import Scene
from engine.game_object import GameObject


def test_scene_index_tracks_root_and_children_by_stable_identity():
    scene = Scene()
    root = GameObject("Root", tag="World")
    child = root.add_child(GameObject("Child", tag="Enemy"))
    scene.add_game_object(root)
    assert scene.find_by_id(child.id) is child
    assert scene.find("Child") is child
    assert scene.find_by_tag("Enemy") == [child]


def test_scene_index_recovers_from_legacy_direct_rename():
    scene = Scene()
    obj = scene.add_game_object(GameObject("Before"))
    obj.name = "After"
    assert scene.find("After") is obj
    assert scene.find("Before") is None


def test_scene_index_removes_subtree():
    scene = Scene()
    root = GameObject("Root")
    child = root.add_child(GameObject("Child"))
    scene.add_game_object(root)
    scene.remove_game_object(root)
    assert scene.find_by_id(root.id) is None
    assert scene.find_by_id(child.id) is None
