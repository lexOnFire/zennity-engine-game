"""
tests/core/test_game_object.py
────────────────────────────────────────────────────────────────
Commit 6: valida o contrato público de GameObject.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ===========================================================================
# 1. Identidade
# ===========================================================================

class TestIdentity:
    def test_id_is_string(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert isinstance(go.id, str)

    def test_ids_are_unique(self):
        from engine.core import GameObject
        ids = {GameObject("x").id for _ in range(50)}
        assert len(ids) == 50

    def test_short_id_is_8_chars(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert len(go.short_id) == 8

    def test_short_id_is_prefix_of_id(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert go.id.startswith(go.short_id)

    def test_name_set_on_init(self):
        from engine.core import GameObject
        go = GameObject("Hero")
        assert go.name == "Hero"

    def test_tag_default_untagged(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert go.tag == "Untagged"

    def test_tag_custom(self):
        from engine.core import GameObject
        go = GameObject("A", tag="Enemy")
        assert go.tag == "Enemy"

    def test_active_default_true(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert go.active is True


# ===========================================================================
# 2. Transform automático
# ===========================================================================

class TestAutoTransform:
    def test_transform_exists(self):
        from engine.core import GameObject, Transform
        go = GameObject("A")
        assert isinstance(go.transform, Transform)

    def test_transform_in_components(self):
        from engine.core import GameObject, Transform
        go = GameObject("A")
        assert go.get_component(Transform) is go.transform


# ===========================================================================
# 3. Components
# ===========================================================================

class TestComponents:
    def test_add_component_returns_it(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        comp = Component()
        result = go.add_component(comp)
        assert result is comp

    def test_add_component_sets_game_object(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        comp = go.add_component(Component())
        assert comp.game_object is go

    def test_get_component_returns_correct_type(self):
        from engine.core import Component, GameObject

        class Hp(Component): pass
        go = GameObject("A")
        hp = go.add_component(Hp())
        assert go.get_component(Hp) is hp

    def test_get_component_returns_none_if_absent(self):
        from engine.core import Component, GameObject

        class Missing(Component): pass
        go = GameObject("A")
        assert go.get_component(Missing) is None

    def test_get_components_returns_all_of_type(self):
        from engine.core import Component, GameObject

        class Bullet(Component): pass
        go = GameObject("A")
        b1 = go.add_component(Bullet())
        b2 = go.add_component(Bullet())
        result = go.get_components(Bullet)
        assert b1 in result and b2 in result
        assert len(result) == 2

    def test_remove_component_detaches_game_object(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        comp = go.add_component(Component())
        go.remove_component(comp)
        assert comp.game_object is None

    def test_remove_component_calls_destroy(self):
        from engine.core import Component, GameObject

        class Spy(Component):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            def destroy(self):
                self.destroyed = True

        go = GameObject("A")
        spy = go.add_component(Spy())
        go.remove_component(spy)
        assert spy.destroyed is True

    def test_remove_component_removes_from_list(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        comp = go.add_component(Component())
        go.remove_component(comp)
        assert comp not in go.components

    def test_remove_nonexistent_component_is_safe(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        comp = Component()
        go.remove_component(comp)  # nunca adicionado — não deve lançar


# ===========================================================================
# 4. Hierarquia
# ===========================================================================

class TestHierarchy:
    def test_add_child_sets_parent(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        assert child.parent is parent

    def test_add_child_appears_in_children(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        assert child in parent.children

    def test_remove_child_clears_parent(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.remove_child(child)
        assert child.parent is None

    def test_remove_child_removes_from_children(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.remove_child(child)
        assert child not in parent.children

    def test_reparent_removes_from_old_parent(self):
        from engine.core import GameObject
        p1 = GameObject("P1")
        p2 = GameObject("P2")
        child = GameObject("C")
        p1.add_child(child)
        p2.add_child(child)  # reparent
        assert child not in p1.children
        assert child in p2.children
        assert child.parent is p2

    def test_child_inherits_scene_from_parent(self):
        from engine.core import GameObject, Scene
        scene  = Scene()
        parent = GameObject("P")
        child  = GameObject("C")
        scene.add_game_object(parent)
        parent.add_child(child)
        assert child.scene is scene

    def test_remove_child_clears_scene(self):
        from engine.core import GameObject, Scene
        scene  = Scene()
        parent = GameObject("P")
        child  = GameObject("C")
        scene.add_game_object(parent)
        parent.add_child(child)
        parent.remove_child(child)
        assert child.scene is None


# ===========================================================================
# 5. active
# ===========================================================================

class TestActive:
    def test_inactive_go_skips_update(self):
        from engine.core import Component, GameObject

        class Ticker(Component):
            def __init__(self):
                super().__init__()
                self.ticks = 0
            def update(self, dt): self.ticks += 1

        go = GameObject("A")
        t = go.add_component(Ticker())
        go.active = False
        go.update(0.016)
        assert t.ticks == 0

    def test_inactive_go_skips_draw(self):
        from engine.core import Component, GameObject

        class Drawer(Component):
            def __init__(self):
                super().__init__()
                self.drawn = False
            def draw(self, screen): self.drawn = True

        go = GameObject("A")
        d = go.add_component(Drawer())
        go.active = False
        go.draw(MagicMock())
        assert d.drawn is False


# ===========================================================================
# 6. destroy
# ===========================================================================

class TestDestroy:
    def test_destroy_sets_active_false(self):
        from engine.core import GameObject
        go = GameObject("A")
        go.destroy()
        assert go.active is False

    def test_destroy_clears_components(self):
        from engine.core import Component, GameObject
        go = GameObject("A")
        go.add_component(Component())
        go.destroy()
        assert len(go.components) == 0

    def test_destroy_clears_children(self):
        from engine.core import GameObject
        parent = GameObject("P")
        parent.add_child(GameObject("C"))
        parent.destroy()
        assert len(parent.children) == 0

    def test_destroy_removes_from_parent(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        child.destroy()
        assert child not in parent.children

    def test_destroy_calls_component_destroy(self):
        from engine.core import Component, GameObject

        class Spy(Component):
            def __init__(self):
                super().__init__()
                self.destroyed = False
            def destroy(self): self.destroyed = True

        go = GameObject("A")
        spy = go.add_component(Spy())
        go.destroy()
        assert spy.destroyed is True


# ===========================================================================
# 7. __repr__
# ===========================================================================

class TestRepr:
    def test_repr_contains_name(self):
        from engine.core import GameObject
        go = GameObject("Sword")
        assert "Sword" in repr(go)

    def test_repr_contains_short_id(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert go.short_id in repr(go)

    def test_repr_contains_tag_when_not_untagged(self):
        from engine.core import GameObject
        go = GameObject("A", tag="Player")
        assert "Player" in repr(go)

    def test_repr_omits_tag_when_untagged(self):
        from engine.core import GameObject
        go = GameObject("A")
        assert "Untagged" not in repr(go)
