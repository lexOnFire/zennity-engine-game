"""
tests/physics/test_collider.py
────────────────────────────────────────────────────────────────
Suite completa de BoxCollider e CircleCollider — 72 testes.

Estratégia de isolamento:
  - BoxCollider._registry e CircleCollider._registry são listas de CLASS.
    A fixture autouse limpa ambas antes e depois de cada teste.
  - RigidBody é mocado inline: `rb.is_kinematic = False` e `rb.velocity`
    são atribuítos simples em MagicMock, sem import do módulo real.
  - GameObject/Scene/Transform são stubs mínimos: evitam qualquer
    dependência de pygame.Surface ou sprite.
  - Nenhum patch global de pygame é necessário — o import de pygame
    usado em rect() e draw() é mantido mas draw() nunca é chamado aqui.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pygame
import pytest

pygame.init()  # necessário para pygame.Rect funcionar sem display

from engine.physics.collider import BoxCollider, CircleCollider, CollisionInfo


# ---------------------------------------------------------------------------
# Stubs mínimos
# ---------------------------------------------------------------------------

def _make_transform(x: float = 0.0, y: float = 0.0):
    t = MagicMock()
    t.position = [x, y]
    t.get_world_position.return_value = [x, y]
    return t


def _make_rb(vx: float = 0.0, vy: float = 0.0, kinematic: bool = False):
    rb = MagicMock()
    rb.is_kinematic = kinematic
    rb.velocity = [vx, vy]
    return rb


def _make_go(x: float = 0.0, y: float = 0.0, active: bool = True, scene=None,
             rb=None):
    """
    Cria um GameObject stub com transform e get_component() configurado.
    """
    go = MagicMock()
    go.active = active
    go.scene = scene or MagicMock()
    go.transform = _make_transform(x, y)

    def _get_component(cls):
        from engine.physics.rigidbody import RigidBody  # import real
        if cls is RigidBody:
            return rb
        return None

    go.get_component.side_effect = _get_component
    return go


def _box(x=0.0, y=0.0, w=32.0, h=32.0, ox=0.0, oy=0.0,
         trigger=False, rb=None, scene=None, active=True) -> BoxCollider:
    c = BoxCollider(width=w, height=h, offset_x=ox, offset_y=oy,
                    is_trigger=trigger)
    c.game_object = _make_go(x, y, active=active, rb=rb, scene=scene)
    return c


def _circle(x=0.0, y=0.0, r=16.0, ox=0.0, oy=0.0,
            trigger=False, rb=None, scene=None, active=True) -> CircleCollider:
    c = CircleCollider(radius=r, offset_x=ox, offset_y=oy, is_trigger=trigger)
    c.game_object = _make_go(x, y, active=active, rb=rb, scene=scene)
    return c


# ---------------------------------------------------------------------------
# Fixture de isolamento
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_registries():
    BoxCollider._registry.clear()
    BoxCollider._scene_tilemaps.clear()
    BoxCollider._scene_tilemap_components.clear()
    BoxCollider._checks_count = 0
    CircleCollider._registry.clear()
    CircleCollider._checks_count = 0
    yield
    BoxCollider._registry.clear()
    BoxCollider._scene_tilemaps.clear()
    BoxCollider._scene_tilemap_components.clear()
    CircleCollider._registry.clear()


# ===========================================================================
# 1. CollisionInfo
# ===========================================================================
class TestCollisionInfo:
    def test_fields_stored(self):
        other = MagicMock()
        info = CollisionInfo(other=other, overlap_x=5.0, overlap_y=3.0)
        assert info.other is other
        assert info.overlap_x == pytest.approx(5.0)
        assert info.overlap_y == pytest.approx(3.0)

    def test_defaults_zero(self):
        info = CollisionInfo(other=MagicMock())
        assert info.overlap_x == 0.0
        assert info.overlap_y == 0.0

    def test_is_dataclass(self):
        import dataclasses
        assert dataclasses.is_dataclass(CollisionInfo)

    def test_other_can_be_any_object(self):
        sentinel = object()
        info = CollisionInfo(other=sentinel)
        assert info.other is sentinel


# ===========================================================================
# 2. BoxCollider — construtor
# ===========================================================================
class TestBoxColliderInit:
    def test_default_size(self):
        c = BoxCollider()
        assert c.width == 32.0
        assert c.height == 32.0

    def test_custom_size(self):
        c = BoxCollider(width=64.0, height=48.0)
        assert c.width == 64.0
        assert c.height == 48.0

    def test_default_offset_zero(self):
        c = BoxCollider()
        assert c.offset_x == 0.0
        assert c.offset_y == 0.0

    def test_custom_offset(self):
        c = BoxCollider(offset_x=10.0, offset_y=-5.0)
        assert c.offset_x == 10.0
        assert c.offset_y == -5.0

    def test_is_trigger_default_false(self):
        assert BoxCollider().is_trigger is False

    def test_is_trigger_true(self):
        c = BoxCollider(is_trigger=True)
        assert c.is_trigger is True

    def test_callbacks_default_none(self):
        c = BoxCollider()
        assert c.on_collision_enter is None
        assert c.on_collision_exit is None


# ===========================================================================
# 3. BoxCollider — ciclo de vida
# ===========================================================================
class TestBoxColliderLifecycle:
    def test_start_registers_collider(self):
        c = BoxCollider()
        c.start()
        assert c in BoxCollider._registry

    def test_start_does_not_duplicate(self):
        c = BoxCollider()
        c.start()
        c.start()
        assert BoxCollider._registry.count(c) == 2  # start não deduplica (por design)

    def test_destroy_removes_from_registry(self):
        c = BoxCollider()
        c.start()
        c.destroy()
        assert c not in BoxCollider._registry

    def test_destroy_when_not_registered_is_safe(self):
        c = BoxCollider()
        c.destroy()  # sem crash

    def test_multiple_colliders_all_registered(self):
        for _ in range(5):
            c = BoxCollider()
            c.start()
        assert len(BoxCollider._registry) == 5


# ===========================================================================
# 4. BoxCollider — rect
# ===========================================================================
class TestBoxColliderRect:
    def test_rect_without_game_object(self):
        c = BoxCollider(width=32, height=32)
        r = c.rect
        assert isinstance(r, pygame.Rect)
        assert r.topleft == (0, 0)
        assert r.size == (32, 32)

    def test_rect_with_game_object_centered(self):
        c = _box(x=100, y=80, w=40, h=20)
        assert c.rect == pygame.Rect(80, 70, 40, 20)

    def test_rect_with_offset(self):
        c = _box(x=100, y=80, w=40, h=20, ox=10, oy=-5)
        assert c.rect == pygame.Rect(90, 65, 40, 20)

    def test_rect_int_conversion(self):
        c = _box(x=10.7, y=20.9, w=5.5, h=6.5)
        assert isinstance(c.rect.left, int)
        assert isinstance(c.rect.width, int)

    def test_rect_updates_when_transform_moves(self):
        c = _box(x=50, y=50, w=20, h=20)
        c.game_object.transform.get_world_position.return_value = [70, 70]
        assert c.rect.topleft == (60, 60)

    def test_rect_negative_coords(self):
        c = _box(x=-10, y=-10, w=20, h=20)
        assert c.rect.topleft == (-20, -20)


# ===========================================================================
# 5. BoxCollider — check_all básico
# ===========================================================================
class TestBoxCheckAllBasic:
    def test_no_collision_no_callbacks(self):
        scene = MagicMock()
        a = _box(0, 0, scene=scene)
        b = _box(200, 0, scene=scene)
        a.on_collision_enter = MagicMock()
        b.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        a.on_collision_enter.assert_not_called()
        b.on_collision_enter.assert_not_called()

    def test_collision_enter_callbacks(self):
        scene = MagicMock()
        a = _box(0, 0, w=20, h=20, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        a.on_collision_enter = MagicMock()
        b.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        assert b in a._colliding_with
        assert a in b._colliding_with
        a.on_collision_enter.assert_called_once()
        b.on_collision_enter.assert_called_once()
        info = a.on_collision_enter.call_args.args[0]
        assert isinstance(info, CollisionInfo)
        assert info.other is b

    def test_enter_only_once_while_still_colliding(self):
        scene = MagicMock()
        a = _box(0, 0, w=20, h=20, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        a.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        BoxCollider.check_all()
        a.on_collision_enter.assert_called_once()

    def test_exit_callback_when_separated(self):
        scene = MagicMock()
        a = _box(0, 0, w=20, h=20, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        a.on_collision_exit = MagicMock()
        b.on_collision_exit = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        b.game_object.transform.get_world_position.return_value = [100, 0]
        BoxCollider.check_all()
        a.on_collision_exit.assert_called_once_with(b)
        b.on_collision_exit.assert_called_once_with(a)

    def test_inactive_object_ignored(self):
        scene = MagicMock()
        a = _box(0, 0, scene=scene)
        b = _box(0, 0, scene=scene, active=False)
        a.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        a.on_collision_enter.assert_not_called()

    def test_different_scenes_ignored(self):
        a = _box(0, 0, scene=MagicMock())
        b = _box(0, 0, scene=MagicMock())
        a.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        a.on_collision_enter.assert_not_called()

    def test_none_scene_ignored(self):
        a = _box(0, 0, scene=None)
        b = _box(0, 0, scene=None)
        a.game_object.scene = None
        b.game_object.scene = None
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()  # sem crash

    def test_orphan_purged_every_60_checks(self):
        c = BoxCollider()
        c.game_object = None
        BoxCollider._registry.append(c)
        for _ in range(60):
            BoxCollider.check_all()
        assert c not in BoxCollider._registry


# ===========================================================================
# 6. BoxCollider — trigger
# ===========================================================================
class TestBoxCheckAllTrigger:
    def test_trigger_detects_but_does_not_resolve(self):
        scene = MagicMock()
        rb = _make_rb()
        a = _box(0, 0, w=20, h=20, trigger=True, rb=rb, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        orig = list(a.game_object.transform.position)
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        assert b in a._colliding_with
        assert a.game_object.transform.position == orig

    def test_non_trigger_resolves_with_rigidbody(self):
        scene = MagicMock()
        rb = _make_rb(vx=10)
        a = _box(0, 0, w=20, h=20, rb=rb, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        assert a.game_object.transform.position[0] != 0


# ===========================================================================
# 7. BoxCollider — _resolve
# ===========================================================================
class TestBoxResolve:
    def test_resolve_returns_if_no_rigidbody(self):
        a = _box(0, 0)
        b = _box(10, 0)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position == [0, 0]
        assert b.game_object.transform.position == [10, 0]

    def test_resolve_dynamic_a_only_x(self):
        rb = _make_rb(vx=5)
        a = _box(0, 0, rb=rb)
        b = _box(10, 0)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position[0] < 0
        assert rb.velocity[0] == 0

    def test_resolve_dynamic_b_only_x(self):
        rb = _make_rb(vx=-5)
        a = _box(0, 0)
        b = _box(10, 0, rb=rb)
        BoxCollider._resolve(a, b, 10, 20)
        assert b.game_object.transform.position[0] > 10
        assert rb.velocity[0] == 0

    def test_resolve_both_dynamic_share(self):
        rb_a = _make_rb(vx=5)
        rb_b = _make_rb(vx=-5)
        a = _box(0, 0, rb=rb_a)
        b = _box(10, 0, rb=rb_b)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position[0] == pytest.approx(-5)
        assert b.game_object.transform.position[0] == pytest.approx(15)

    def test_resolve_y_axis(self):
        rb = _make_rb(vy=5)
        a = _box(0, 0, rb=rb)
        b = _box(0, 10)
        BoxCollider._resolve(a, b, 20, 10)
        assert a.game_object.transform.position[1] < 0
        assert rb.velocity[1] == 0

    def test_kinematic_ignored(self):
        rb = _make_rb(vx=5, kinematic=True)
        a = _box(0, 0, rb=rb)
        b = _box(10, 0)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position == [0, 0]


# ===========================================================================
# 8. CircleCollider — construtor/centro/check_all/_resolve
# ===========================================================================
class TestCircleCollider:
    def test_init_defaults(self):
        c = CircleCollider()
        assert c.radius == 16.0
        assert c.offset_x == 0.0
        assert c.offset_y == 0.0
        assert c.is_trigger is False

    def test_center_without_go(self):
        c = CircleCollider(offset_x=2, offset_y=3)
        assert c.center == (2, 3)

    def test_center_with_go(self):
        c = _circle(10, 20, ox=2, oy=-3)
        assert c.center == (12.0, 17.0)

    def test_collision_enter_and_exit(self):
        scene = MagicMock()
        a = _circle(0, 0, r=10, scene=scene)
        b = _circle(15, 0, r=10, scene=scene)
        a.on_collision_enter = MagicMock()
        a.on_collision_exit = MagicMock()
        CircleCollider._registry.extend([a, b])
        CircleCollider.check_all()
        a.on_collision_enter.assert_called_once_with(b)
        b.game_object.transform.get_world_position.return_value = [100, 0]
        CircleCollider.check_all()
        a.on_collision_exit.assert_called_once_with(b)

    def test_trigger_does_not_resolve(self):
        scene = MagicMock()
        rb = _make_rb()
        a = _circle(0, 0, r=10, trigger=True, rb=rb, scene=scene)
        b = _circle(15, 0, r=10, scene=scene)
        orig = list(a.game_object.transform.position)
        CircleCollider._registry.extend([a, b])
        CircleCollider.check_all()
        assert b in a._colliding_with
        assert a.game_object.transform.position == orig

    def test_resolve_dist_zero_fallback(self):
        rb = _make_rb(vx=5)
        a = _circle(0, 0, r=10, rb=rb)
        b = _circle(0, 0, r=10)
        CircleCollider._resolve(a, b, 0, 0, 0, 0, 0, 20)
        assert a.game_object.transform.position[0] < 0
        assert rb.velocity[0] == 0
