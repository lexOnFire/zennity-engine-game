"""
tests/test_game_object.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/game_object.py.

Estratégia de isolamento:
  - pygame stubado via sys.modules (go.draw exige Surface).
  - Component real importado (engine/component.py é puro Python).
  - Scene é MagicMock — usada apenas para verificar que start() é
    chamado quando scene está presente.
  - Componentes concretos definidos localmente (_Counter, _Crasher)
    para testar comportamentos específicos sem import externo.
"""
from __future__ import annotations

import sys
import uuid
from types import ModuleType
from unittest.mock import MagicMock


# ── stub pygame ──────────────────────────────────────────────────────────────
if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    _pg.Surface = MagicMock
    sys.modules["pygame"] = _pg

from engine.game_object import GameObject   # noqa: E402
from engine.component import Component, Transform  # noqa: E402


# ── componentes auxiliares ─────────────────────────────────────────────────────────

class _Counter(Component):
    """Component que conta chamadas a start/update/draw/destroy."""
    def __init__(self):
        super().__init__()
        self.started = 0
        self.updated = 0
        self.drawn   = 0
        self.destroyed_flag = False

    def start(self):   self.started  += 1
    def update(self, dt): self.updated += 1
    def draw(self, screen): self.drawn  += 1
    def destroy(self): self.destroyed_flag = True


class _Crasher(Component):
    """Component que lança na update."""
    def update(self, dt): raise RuntimeError("boom")


class _TypeA(Component): pass
class _TypeB(Component): pass


# ── helpers ──────────────────────────────────────────────────────────────────

def _go(name="GO", tag="Untagged"):
    return GameObject(name=name, tag=tag)


def _screen():
    return MagicMock()


# ── TestInit ────────────────────────────────────────────────────────────────
class TestInit:
    def test_name_stored(self):
        assert _go("Player").name == "Player"

    def test_default_name(self):
        assert GameObject().name == "GameObject"

    def test_tag_stored(self):
        assert _go(tag="Enemy").tag == "Enemy"

    def test_default_tag(self):
        assert _go().tag == "Untagged"

    def test_active_true_by_default(self):
        assert _go().active is True

    def test_parent_none(self):
        assert _go().parent is None

    def test_children_empty(self):
        assert _go().children == []

    def test_scene_none(self):
        assert _go().scene is None

    def test_id_is_valid_uuid4(self):
        go = _go()
        parsed = uuid.UUID(go.id, version=4)
        assert str(parsed) == go.id

    def test_id_unique_per_instance(self):
        assert _go().id != _go().id

    def test_short_id_length(self):
        assert len(_go().short_id) == 8

    def test_transform_added_automatically(self):
        go = _go()
        assert go.get_component(Transform) is go.transform

    def test_transform_game_object_is_self(self):
        go = _go()
        assert go.transform.game_object is go


# ── TestComponents ────────────────────────────────────────────────────────────
class TestComponents:
    def test_add_component_returns_component(self):
        go = _go()
        c = _Counter()
        assert go.add_component(c) is c

    def test_add_component_sets_game_object(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        assert c.game_object is go

    def test_add_component_appended_to_list(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        assert c in go.components

    def test_get_component_found(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        assert go.get_component(_Counter) is c

    def test_get_component_not_found_returns_none(self):
        go = _go()
        assert go.get_component(_TypeA) is None

    def test_get_component_returns_first_match(self):
        go = _go()
        c1, c2 = _Counter(), _Counter()
        go.add_component(c1)
        go.add_component(c2)
        assert go.get_component(_Counter) is c1

    def test_get_components_returns_all(self):
        go = _go()
        c1, c2 = _Counter(), _Counter()
        go.add_component(c1)
        go.add_component(c2)
        result = go.get_components(_Counter)
        assert c1 in result and c2 in result and len(result) == 2

    def test_get_components_empty_list_if_none(self):
        go = _go()
        assert go.get_components(_TypeA) == []

    def test_get_components_filters_by_type(self):
        go = _go()
        go.add_component(_TypeA())
        go.add_component(_TypeB())
        result = go.get_components(_TypeA)
        assert len(result) == 1
        assert isinstance(result[0], _TypeA)

    def test_remove_component_removes_from_list(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.remove_component(c)
        assert c not in go.components

    def test_remove_component_calls_destroy(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.remove_component(c)
        assert c.destroyed_flag is True

    def test_remove_component_clears_game_object(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.remove_component(c)
        assert c.game_object is None

    def test_remove_component_not_present_no_crash(self):
        go = _go()
        go.remove_component(_Counter())  # não adicionado

    def test_start_called_when_scene_present(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.scene = MagicMock()  # aciona start nos components
        assert c.started == 1

    def test_start_not_called_twice(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        scene = MagicMock()
        go.scene = scene
        go.scene = scene  # segunda atribuição não deve re-chamar start
        assert c.started == 1


# ── TestLifecycle ───────────────────────────────────────────────────────────────
class TestLifecycle:
    def test_update_calls_all_components(self):
        go = _go()
        c1, c2 = _Counter(), _Counter()
        go.add_component(c1)
        go.add_component(c2)
        go.update(0.016)
        assert c1.updated == 1 and c2.updated == 1

    def test_update_inactive_skips_components(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.active = False
        go.update(0.016)
        assert c.updated == 0

    def test_update_propagates_to_children(self):
        parent = _go()
        child  = _go()
        c = _Counter()
        child.add_component(c)
        parent.add_child(child)
        parent.update(0.016)
        assert c.updated == 1

    def test_update_inactive_child_skipped(self):
        parent = _go()
        child  = _go()
        c = _Counter()
        child.add_component(c)
        parent.add_child(child)
        child.active = False
        parent.update(0.016)
        assert c.updated == 0

    def test_draw_calls_all_components(self):
        go = _go()
        c1, c2 = _Counter(), _Counter()
        go.add_component(c1)
        go.add_component(c2)
        go.draw(_screen())
        assert c1.drawn == 1 and c2.drawn == 1

    def test_draw_inactive_skips(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.active = False
        go.draw(_screen())
        assert c.drawn == 0

    def test_draw_propagates_to_children(self):
        parent = _go()
        child  = _go()
        c = _Counter()
        child.add_component(c)
        parent.add_child(child)
        parent.draw(_screen())
        assert c.drawn == 1

    def test_destroy_deactivates(self):
        go = _go()
        go.destroy()
        assert go.active is False

    def test_destroy_calls_component_destroy(self):
        go = _go()
        c = _Counter()
        go.add_component(c)
        go.destroy()
        assert c.destroyed_flag is True

    def test_destroy_clears_components(self):
        go = _go()
        go.add_component(_Counter())
        go.destroy()
        assert go.components == []

    def test_destroy_clears_children(self):
        parent = _go()
        parent.add_child(_go())
        parent.destroy()
        assert parent.children == []

    def test_destroy_removes_from_parent(self):
        parent = _go()
        child  = _go()
        parent.add_child(child)
        child.destroy()
        assert child not in parent.children

    def test_destroy_child_recursively(self):
        parent = _go()
        child  = _go()
        c = _Counter()
        child.add_component(c)
        parent.add_child(child)
        parent.destroy()
        assert c.destroyed_flag is True


# ── TestHierarchy ────────────────────────────────────────────────────────────────
class TestHierarchy:
    def test_add_child_sets_parent(self):
        parent, child = _go(), _go()
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_appends_to_children(self):
        parent, child = _go(), _go()
        parent.add_child(child)
        assert child in parent.children

    def test_add_child_returns_child(self):
        parent, child = _go(), _go()
        assert parent.add_child(child) is child

    def test_add_child_reparents_if_already_has_parent(self):
        p1, p2, child = _go(), _go(), _go()
        p1.add_child(child)
        p2.add_child(child)
        assert child.parent is p2
        assert child not in p1.children

    def test_remove_child_clears_parent(self):
        parent, child = _go(), _go()
        parent.add_child(child)
        parent.remove_child(child)
        assert child.parent is None

    def test_remove_child_removes_from_children(self):
        parent, child = _go(), _go()
        parent.add_child(child)
        parent.remove_child(child)
        assert child not in parent.children

    def test_remove_child_not_present_no_crash(self):
        parent = _go()
        parent.remove_child(_go())  # nunca adicionado

    def test_add_child_propagates_scene(self):
        parent = _go()
        parent._scene = MagicMock()
        child = _go()
        c = _Counter()
        child.add_component(c)
        parent.add_child(child)
        # child.scene deve ser o scene do parent
        assert child.scene is parent.scene

    def test_remove_child_clears_scene(self):
        parent = _go()
        parent._scene = MagicMock()
        child = _go()
        parent.add_child(child)
        parent.remove_child(child)
        assert child.scene is None

    def test_multiple_children(self):
        parent = _go()
        children = [_go() for _ in range(5)]
        for c in children:
            parent.add_child(c)
        assert len(parent.children) == 5


# ── TestRepr ───────────────────────────────────────────────────────────────────
class TestRepr:
    def test_repr_contains_name(self):
        assert "Player" in repr(_go("Player"))

    def test_repr_contains_short_id(self):
        go = _go()
        assert go.short_id in repr(go)

    def test_repr_shows_tag_when_not_untagged(self):
        assert "Enemy" in repr(_go(tag="Enemy"))

    def test_repr_omits_tag_when_untagged(self):
        assert "Untagged" not in repr(_go())
