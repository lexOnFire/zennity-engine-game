"""
tests/core/test_game_object.py
─────────────────────────────────────────────────────────────────
Testes unitários de engine/game_object.py.

Estratégia:
  - pygame não é inicializado (Surface é mockada onde necessário).
  - Scene é simulada com MagicMock para testar propagação sem depender
    da implementação real da cena.
  - Cada teste cria seus próprios objetos — sem estado compartilhado.
"""
from __future__ import annotations

import re
from unittest.mock import MagicMock, call, patch

import pytest

from engine.game_object import GameObject
from engine.core.component import Component, Transform


# ─────────────────────────────────────────────────────────────────
def make_component() -> Component:
    """Cria um Component concreto simples para testes."""
    comp = Component()
    comp.start   = MagicMock()
    comp.update  = MagicMock()
    comp.draw    = MagicMock()
    comp.destroy = MagicMock()
    return comp


def fake_scene() -> MagicMock:
    """Simula uma Scene suficiente para ativar start()."""
    return MagicMock(spec=["__class__", "name"])


# ─────────────────────────────────────────────────────────────────
class TestIdentity:
    def test_default_name(self):
        assert GameObject().name == "GameObject"

    def test_custom_name(self):
        assert GameObject("Player").name == "Player"

    def test_default_tag(self):
        assert GameObject().tag == "Untagged"

    def test_custom_tag(self):
        assert GameObject("E", tag="Enemy").tag == "Enemy"

    def test_id_is_uuid4_format(self):
        go = GameObject()
        assert re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            go.id,
        ), f"ID não parece UUID4: {go.id}"

    def test_ids_are_unique(self):
        ids = {GameObject().id for _ in range(100)}
        assert len(ids) == 100

    def test_short_id_is_8_chars(self):
        assert len(GameObject().short_id) == 8

    def test_short_id_is_prefix_of_id(self):
        go = GameObject()
        assert go.id.startswith(go.short_id)

    def test_active_default_true(self):
        assert GameObject().active is True

    def test_repr_contains_name(self):
        go = GameObject("Hero")
        assert "Hero" in repr(go)

    def test_repr_contains_short_id(self):
        go = GameObject()
        assert go.short_id in repr(go)

    def test_repr_no_tag_for_untagged(self):
        go = GameObject()
        assert "tag=" not in repr(go)

    def test_repr_has_tag_when_set(self):
        go = GameObject(tag="Player")
        assert "tag=Player" in repr(go)


# ─────────────────────────────────────────────────────────────────
class TestTransform:
    def test_has_transform_on_init(self):
        go = GameObject()
        assert isinstance(go.transform, Transform)

    def test_transform_is_in_components(self):
        go = GameObject()
        assert go.transform in go.components

    def test_transform_game_object_set(self):
        go = GameObject()
        assert go.transform.game_object is go

    def test_transform_default_position(self):
        go = GameObject()
        assert go.transform.x == 0.0
        assert go.transform.y == 0.0


# ─────────────────────────────────────────────────────────────────
class TestAddComponent:
    def test_add_component_sets_game_object(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        assert comp.game_object is go

    def test_add_component_appends_to_list(self):
        go   = GameObject()
        comp = make_component()
        before = len(go.components)
        go.add_component(comp)
        assert len(go.components) == before + 1

    def test_add_component_returns_component(self):
        go   = GameObject()
        comp = make_component()
        assert go.add_component(comp) is comp

    def test_add_component_calls_start_when_scene_set(self):
        go        = GameObject()
        go._scene = fake_scene()
        comp      = make_component()
        go.add_component(comp)
        comp.start.assert_called_once()

    def test_add_component_no_start_without_scene(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        comp.start.assert_not_called()

    def test_add_multiple_components(self):
        go = GameObject()
        a  = go.add_component(make_component())
        b  = go.add_component(make_component())
        assert a in go.components
        assert b in go.components


# ─────────────────────────────────────────────────────────────────
class TestGetComponent:
    def test_get_component_returns_matching(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        assert go.get_component(Component) is comp

    def test_get_component_returns_none_when_missing(self):
        go = GameObject()
        class Foo(Component): pass
        assert go.get_component(Foo) is None

    def test_get_component_returns_first_match(self):
        go = GameObject()
        a  = make_component()
        b  = make_component()
        go.add_component(a)
        go.add_component(b)
        result = go.get_component(Component)
        # Transform é o primeiro Component na lista
        assert isinstance(result, Component)

    def test_get_components_returns_all(self):
        go = GameObject()
        a  = make_component()
        b  = make_component()
        go.add_component(a)
        go.add_component(b)
        results = go.get_components(Component)
        assert a in results
        assert b in results

    def test_get_component_uses_isinstance(self):
        """Transform é subclasse de Component, deve ser encontrado."""
        go = GameObject()
        assert go.get_component(Transform) is go.transform


# ─────────────────────────────────────────────────────────────────
class TestRemoveComponent:
    def test_remove_component_removes_from_list(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.remove_component(comp)
        assert comp not in go.components

    def test_remove_component_calls_destroy(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.remove_component(comp)
        comp.destroy.assert_called_once()

    def test_remove_component_detaches_game_object(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.remove_component(comp)
        assert comp.game_object is None

    def test_remove_nonexistent_component_no_error(self):
        go   = GameObject()
        comp = make_component()
        go.remove_component(comp)  # nunca foi adicionado


# ─────────────────────────────────────────────────────────────────
class TestHierarchy:
    def test_add_child_sets_parent(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_appends_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        assert child in parent.children

    def test_add_child_returns_child(self):
        parent = GameObject("P")
        child  = GameObject("C")
        assert parent.add_child(child) is child

    def test_add_child_reparents_from_previous(self):
        old    = GameObject("Old")
        new    = GameObject("New")
        child  = GameObject("C")
        old.add_child(child)
        new.add_child(child)
        assert child.parent is new
        assert child not in old.children
        assert child in new.children

    def test_remove_child_clears_parent(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.remove_child(child)
        assert child.parent is None

    def test_remove_child_removes_from_list(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.remove_child(child)
        assert child not in parent.children

    def test_remove_child_propagates_scene_none(self):
        parent        = GameObject("P")
        parent._scene = fake_scene()
        child         = GameObject("C")
        parent.add_child(child)
        parent.remove_child(child)
        assert child.scene is None

    def test_add_child_propagates_scene(self):
        scene         = fake_scene()
        parent        = GameObject("P")
        parent._scene = scene
        child         = GameObject("C")
        parent.add_child(child)
        assert child.scene is scene


# ─────────────────────────────────────────────────────────────────
class TestUpdate:
    def test_update_calls_component_update(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.update(0.016)
        comp.update.assert_called_once_with(0.016)

    def test_update_propagates_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        comp   = make_component()
        child.add_component(comp)
        parent.add_child(child)
        parent.update(0.016)
        comp.update.assert_called_once_with(0.016)

    def test_update_skipped_when_inactive(self):
        go      = GameObject()
        comp    = make_component()
        go.add_component(comp)
        go.active = False
        go.update(0.016)
        comp.update.assert_not_called()

    def test_update_does_not_propagate_to_inactive_children(self):
        parent        = GameObject("P")
        child         = GameObject("C")
        comp          = make_component()
        child.add_component(comp)
        child.active  = False
        parent.add_child(child)
        parent.update(0.016)
        comp.update.assert_not_called()


# ─────────────────────────────────────────────────────────────────
class TestDraw:
    def test_draw_calls_component_draw(self):
        go      = GameObject()
        comp    = make_component()
        go.add_component(comp)
        screen  = MagicMock()
        go.draw(screen)
        comp.draw.assert_called_once_with(screen)

    def test_draw_propagates_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        comp   = make_component()
        child.add_component(comp)
        parent.add_child(child)
        screen = MagicMock()
        parent.draw(screen)
        comp.draw.assert_called_once_with(screen)

    def test_draw_skipped_when_inactive(self):
        go      = GameObject()
        comp    = make_component()
        go.add_component(comp)
        go.active = False
        go.draw(MagicMock())
        comp.draw.assert_not_called()


# ─────────────────────────────────────────────────────────────────
class TestDestroy:
    def test_destroy_sets_inactive(self):
        go = GameObject()
        go.destroy()
        assert go.active is False

    def test_destroy_calls_component_destroy(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.destroy()
        comp.destroy.assert_called_once()

    def test_destroy_clears_components(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        go.destroy()
        assert len(go.components) == 0

    def test_destroy_propagates_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        comp   = make_component()
        child.add_component(comp)
        parent.add_child(child)
        parent.destroy()
        comp.destroy.assert_called_once()
        assert child.active is False

    def test_destroy_removes_from_parent(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        child.destroy()
        assert child not in parent.children

    def test_destroy_clears_parent_ref(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        child.destroy()
        assert child.parent is None

    def test_destroy_sets_scene_none(self):
        go        = GameObject()
        go._scene = fake_scene()
        go.destroy()
        assert go.scene is None

    def test_destroy_idempotent(self):
        go = GameObject()
        go.destroy()
        go.destroy()  # não deve lançar


# ─────────────────────────────────────────────────────────────────
class TestScenePropagation:
    def test_scene_setter_calls_start_on_unstarted_components(self):
        go        = GameObject()
        comp      = make_component()
        go.add_component(comp)
        go._scene = None           # sem cena ainda
        comp._started = False
        go.scene  = fake_scene()
        comp.start.assert_called_once()

    def test_scene_setter_does_not_restart_started_component(self):
        go   = GameObject()
        comp = make_component()
        go.add_component(comp)
        comp._started = True
        go.scene = fake_scene()
        comp.start.assert_not_called()

    def test_scene_propagates_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        scene = fake_scene()
        parent.scene = scene
        assert child.scene is scene

    def test_scene_none_propagates_to_children(self):
        parent = GameObject("P")
        child  = GameObject("C")
        scene  = fake_scene()
        parent.add_child(child)
        parent.scene = scene
        parent.scene = None
        assert child.scene is None
