from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.core.component import Transform
from engine.core.component_registry import component_registry
from engine.game_object import GameObject


def root_objects(scene: Any) -> list[GameObject]:
    return [
        obj
        for obj in list(getattr(scene, "editable_objects", []))
        if getattr(obj, "parent", None) is None
    ]


def is_descendant(candidate: GameObject, parent: GameObject) -> bool:
    current = getattr(candidate, "parent", None)
    while current is not None:
        if current is parent:
            return True
        current = getattr(current, "parent", None)
    return False


def can_reparent(obj: GameObject, new_parent: GameObject | None) -> bool:
    if new_parent is None:
        return True
    if obj is new_parent:
        return False
    return not is_descendant(new_parent, obj)


def _editable(scene: Any) -> list[GameObject]:
    return getattr(scene, "editable_objects", [])


def _scene_add(scene: Any, obj: GameObject) -> None:
    if obj not in getattr(scene, "game_objects", []):
        if hasattr(scene, "_add_go"):
            scene._add_go(obj)
        else:
            scene.game_objects.append(obj)
            obj.scene = scene
    # FIX: Adiciona a editable_objects APENAS se for root (parent is None)
    # Isso previne que objetos child saiam do grupo ao fazer ações
    if obj not in _editable(scene) and getattr(obj, "parent", None) is None:
        _editable(scene).append(obj)
    obj.scene = scene
    for child in getattr(obj, "children", []):
        _scene_add(scene, child)


def _scene_remove(scene: Any, obj: GameObject) -> None:
    for child in list(getattr(obj, "children", [])):
        _scene_remove(scene, child)
    if obj in _editable(scene):
        _editable(scene).remove(obj)
    if obj in getattr(scene, "game_objects", []):
        scene.game_objects.remove(obj)
    obj.scene = None


def _detach_from_parent(obj: GameObject) -> tuple[GameObject | None, int | None]:
    old_parent = getattr(obj, "parent", None)
    if old_parent is None:
        return None, None
    old_index = old_parent.children.index(obj) if obj in old_parent.children else None
    if obj in old_parent.children:
        old_parent.children.remove(obj)
    obj.parent = None
    return old_parent, old_index


def _attach_to_parent(obj: GameObject, parent: GameObject | None, index: int | None = None) -> None:
    _detach_from_parent(obj)
    if parent is None:
        obj.parent = None
        return
    obj.parent = parent
    if obj in parent.children:
        parent.children.remove(obj)
    if index is None:
        parent.children.append(obj)
    else:
        parent.children.insert(max(0, min(int(index), len(parent.children))), obj)
    obj.scene = parent.scene


def _move_in_list(items: list[GameObject], obj: GameObject, index: int | None) -> None:
    if obj in items:
        items.remove(obj)
    if index is None:
        items.append(obj)
    else:
        items.insert(max(0, min(int(index), len(items))), obj)


def clone_game_object(obj: GameObject, suffix: str = "_copia") -> GameObject:
    clone = GameObject(f"{obj.name}{suffix}", tag=getattr(obj, "tag", "Untagged"))
    clone.active = bool(getattr(obj, "active", True))
    clone.mesh_type = getattr(obj, "mesh_type", None)
    for attr in ("layer", "enabled", "is_static", "sprite_path", "asset_uuid", "color", "material"):
        if hasattr(obj, attr):
            setattr(clone, attr, getattr(obj, attr))
    clone.transform.position = obj.transform.position.copy()
    clone.transform.rotation = obj.transform.rotation.copy()
    clone.transform.scale = obj.transform.scale.copy()

    for component in getattr(obj, "components", []):
        if isinstance(component, Transform):
            continue
        if not hasattr(component, "serialize"):
            continue
        copied = component_registry.create(component.serialize())
        clone.add_component(copied)

    for child in getattr(obj, "children", []):
        clone.add_child(clone_game_object(child, suffix=suffix))
    return clone


@dataclass
class ReparentGameObjectCommand:
    scene: Any
    obj: GameObject
    new_parent: GameObject | None
    new_index: int | None = None
    description: str = "Reparent GameObject"

    def __post_init__(self) -> None:
        self.old_parent = getattr(self.obj, "parent", None)
        self.old_parent_index = (
            self.old_parent.children.index(self.obj)
            if self.old_parent is not None and self.obj in self.old_parent.children
            else None
        )
        roots = _editable(self.scene)
        self.old_root_index = roots.index(self.obj) if self.obj in roots else None

    def execute(self) -> None:
        if not can_reparent(self.obj, self.new_parent):
            return
        _attach_to_parent(self.obj, self.new_parent, self.new_index)
        if self.new_parent is None:
            _move_in_list(_editable(self.scene), self.obj, self.new_index)

    def undo(self) -> None:
        _attach_to_parent(self.obj, self.old_parent, self.old_parent_index)
        if self.old_parent is None:
            _move_in_list(_editable(self.scene), self.obj, self.old_root_index)


@dataclass
class DuplicateGameObjectCommand:
    scene: Any
    source: GameObject
    description: str = "Duplicate GameObject"

    def __post_init__(self) -> None:
        self.clone: GameObject | None = None
        self.parent = getattr(self.source, "parent", None)
        roots = _editable(self.scene)
        self.root_index = roots.index(self.source) + 1 if self.source in roots else None
        if self.parent is not None and self.source in self.parent.children:
            self.child_index = self.parent.children.index(self.source) + 1
        else:
            self.child_index = None

    def execute(self) -> None:
        if self.clone is None:
            self.clone = clone_game_object(self.source)
        _scene_add(self.scene, self.clone)
        _attach_to_parent(self.clone, self.parent, self.child_index)
        if self.parent is None:
            _move_in_list(_editable(self.scene), self.clone, self.root_index)

    def undo(self) -> None:
        if self.clone is None:
            return
        _detach_from_parent(self.clone)
        _scene_remove(self.scene, self.clone)


@dataclass
class DeleteGameObjectCommand:
    scene: Any
    obj: GameObject
    description: str = "Delete GameObject"

    def __post_init__(self) -> None:
        self.parent = getattr(self.obj, "parent", None)
        roots = _editable(self.scene)
        self.root_index = roots.index(self.obj) if self.obj in roots else None
        self.child_index = (
            self.parent.children.index(self.obj)
            if self.parent is not None and self.obj in self.parent.children
            else None
        )

    def execute(self) -> None:
        _detach_from_parent(self.obj)
        _scene_remove(self.scene, self.obj)

    def undo(self) -> None:
        _scene_add(self.scene, self.obj)
        _attach_to_parent(self.obj, self.parent, self.child_index)
        if self.parent is None:
            _move_in_list(_editable(self.scene), self.obj, self.root_index)


@dataclass
class RenameGameObjectCommand:
    obj: GameObject
    new_name: str
    description: str = "Rename GameObject"

    def __post_init__(self) -> None:
        self.old_name = self.obj.name
        self.new_name = self.new_name.strip()

    def execute(self) -> None:
        if self.new_name:
            self.obj.name = self.new_name

    def undo(self) -> None:
        self.obj.name = self.old_name
