"""
tests/core/test_scene.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/core/scene.py.

Estratégia:
  - pygame é mockado via sys.modules (Scene importa pygame apenas para
    type hints de Surface e Event).
  - Engine é simulada com MagicMock — Scene não chama nada nela;
    a referência existe só para testes de atributo.
  - Cada teste cria GameObjects reais para exercitar integração
    Scene ↔ GameObject (propagation de .scene, start, update, draw).
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


# ── stub pygame (Surface + Event para type hints) ───────────────────────
if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    _pg.Surface = MagicMock
    _pg.event   = ModuleType("pygame.event")
    _pg.event.Event = MagicMock
    sys.modules["pygame"]       = _pg
    sys.modules["pygame.event"] = _pg.event
else:
    _pg = sys.modules["pygame"]

from engine.core.scene import Scene      # noqa: E402
from engine.game_object import GameObject  # noqa: E402
from engine.core.component import Component  # noqa: E402


def make_go(name="GO", tag="Untagged") -> GameObject:
    return GameObject(name, tag=tag)


def make_tracked_go(name="GO") -> tuple[GameObject, MagicMock, MagicMock]:
    """GO + mocks de update e draw para verificar propagação."""
    go   = make_go(name)
    comp = Component()
    comp.update = MagicMock()
    comp.draw   = MagicMock()
    go.add_component(comp)
    return go, comp.update, comp.draw


# ─────────────────────────────────────────────────────────────────────────────
class TestSceneInit:
    def test_default_name(self):
        assert Scene().name == "Scene"

    def test_custom_name(self):
        assert Scene("Level1").name == "Level1"

    def test_game_objects_empty(self):
        assert Scene().game_objects == []

    def test_engine_none(self):
        assert Scene().engine is None

    def test_repr_contains_name(self):
        s = Scene("Boss")
        assert "Boss" in repr(s)

    def test_repr_contains_count(self):
        s = Scene()
        s.add_game_object(make_go())
        assert "objects=1" in repr(s)


# ─────────────────────────────────────────────────────────────────────────────
class TestAddGameObject:
    def test_add_appends_go(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        assert go in s.game_objects

    def test_add_returns_go(self):
        s  = Scene()
        go = make_go()
        assert s.add_game_object(go) is go

    def test_add_sets_scene_on_go(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        assert go.scene is s

    def test_add_duplicate_ignored(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        s.add_game_object(go)
        assert s.game_objects.count(go) == 1

    def test_add_multiple(self):
        s  = Scene()
        a, b = make_go("A"), make_go("B")
        s.add_game_object(a)
        s.add_game_object(b)
        assert len(s.game_objects) == 2

    def test_add_triggers_component_start(self):
        s    = Scene()
        go   = make_go()
        comp = Component()
        comp.start = MagicMock()
        go.add_component(comp)
        comp._started = False
        s.add_game_object(go)
        comp.start.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
class TestRemoveGameObject:
    def test_remove_takes_go_out_of_list(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        s.remove_game_object(go)
        assert go not in s.game_objects

    def test_remove_sets_scene_none_on_go(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        s.remove_game_object(go)
        assert go.scene is None

    def test_remove_nonexistent_no_error(self):
        s  = Scene()
        go = make_go()
        s.remove_game_object(go)  # nunca adicionado

    def test_remove_one_of_many(self):
        s    = Scene()
        a, b = make_go("A"), make_go("B")
        s.add_game_object(a)
        s.add_game_object(b)
        s.remove_game_object(a)
        assert a not in s.game_objects
        assert b in s.game_objects


# ─────────────────────────────────────────────────────────────────────────────
class TestFind:
    def test_find_by_name_returns_go(self):
        s  = Scene()
        go = make_go("Player")
        s.add_game_object(go)
        assert s.find("Player") is go

    def test_find_missing_returns_none(self):
        s = Scene()
        assert s.find("Ghost") is None

    def test_find_returns_first_match(self):
        s   = Scene()
        a   = make_go("X")
        b   = make_go("X")
        s.add_game_object(a)
        s.add_game_object(b)
        assert s.find("X") is a

    def test_find_by_tag_returns_all(self):
        s  = Scene()
        e1 = make_go("E1", tag="Enemy")
        e2 = make_go("E2", tag="Enemy")
        p  = make_go("P",  tag="Player")
        for go in (e1, e2, p):
            s.add_game_object(go)
        result = s.find_by_tag("Enemy")
        assert e1 in result
        assert e2 in result
        assert p  not in result

    def test_find_by_tag_empty(self):
        s = Scene()
        assert s.find_by_tag("Missing") == []

    def test_find_by_id_full_uuid(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        assert s.find_by_id(go.id) is go

    def test_find_by_id_short(self):
        s  = Scene()
        go = make_go()
        s.add_game_object(go)
        assert s.find_by_id(go.short_id) is go

    def test_find_by_id_missing_returns_none(self):
        s = Scene()
        assert s.find_by_id("00000000") is None


# ─────────────────────────────────────────────────────────────────────────────
class TestUpdate:
    def test_update_propagates_to_all_gos(self):
        s = Scene()
        go1, upd1, _ = make_tracked_go("A")
        go2, upd2, _ = make_tracked_go("B")
        s.add_game_object(go1)
        s.add_game_object(go2)
        s.update(0.016)
        upd1.assert_called_once_with(0.016)
        upd2.assert_called_once_with(0.016)

    def test_update_skips_inactive_go(self):
        s = Scene()
        go, upd, _ = make_tracked_go()
        go.active = False
        s.add_game_object(go)
        s.update(0.016)
        upd.assert_not_called()

    def test_update_safe_when_go_removed_during_iteration(self):
        """GO removido durante update não deve causar RuntimeError."""
        s  = Scene()
        go = make_go()
        victim = make_go("victim")

        class Remover(Component):
            def update(self, dt):
                s.remove_game_object(victim)

        go.add_component(Remover())
        s.add_game_object(go)
        s.add_game_object(victim)
        s.update(0.016)  # não deve lançar

    def test_update_empty_scene_no_error(self):
        Scene().update(0.016)


# ─────────────────────────────────────────────────────────────────────────────
class TestDraw:
    def test_draw_propagates_to_all_gos(self):
        s = Scene()
        go1, _, drw1 = make_tracked_go("A")
        go2, _, drw2 = make_tracked_go("B")
        s.add_game_object(go1)
        s.add_game_object(go2)
        screen = MagicMock()
        s.draw(screen)
        drw1.assert_called_once_with(screen)
        drw2.assert_called_once_with(screen)

    def test_draw_skips_inactive_go(self):
        s = Scene()
        go, _, drw = make_tracked_go()
        go.active = False
        s.add_game_object(go)
        s.draw(MagicMock())
        drw.assert_not_called()

    def test_draw_empty_scene_no_error(self):
        Scene().draw(MagicMock())


# ─────────────────────────────────────────────────────────────────────────────
class TestLifecycleHooks:
    def test_start_is_noop_by_default(self):
        Scene().start()  # não deve lançar

    def test_on_exit_is_noop_by_default(self):
        Scene().on_exit()  # não deve lançar

    def test_handle_event_is_noop_by_default(self):
        Scene().handle_event(MagicMock())  # não deve lançar

    def test_subclass_can_override_start(self):
        called = []
        class MyScene(Scene):
            def start(self): called.append(True)
        MyScene().start()
        assert called == [True]

    def test_subclass_update_calls_super(self):
        s = Scene()
        go, upd, _ = make_tracked_go()
        s.add_game_object(go)

        class MyScene(Scene):
            def update(self, dt): super().update(dt)

        ms = MyScene()
        ms.game_objects = s.game_objects
        ms.update(0.016)
        upd.assert_called_once_with(0.016)

    def test_subclass_draw_calls_super(self):
        s = Scene()
        go, _, drw = make_tracked_go()
        s.add_game_object(go)
        screen = MagicMock()

        class MyScene(Scene):
            def draw(self, screen): super().draw(screen)

        ms = MyScene()
        ms.game_objects = s.game_objects
        ms.draw(screen)
        drw.assert_called_once_with(screen)


# ─────────────────────────────────────────────────────────────────────────────
class TestEngineRef:
    def test_engine_can_be_set(self):
        s        = Scene()
        engine   = MagicMock()
        s.engine = engine
        assert s.engine is engine

    def test_engine_default_none(self):
        assert Scene().engine is None
