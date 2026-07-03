"""Testes unitários de engine.physics.collider."""
from __future__ import annotations

import dataclasses
import sys
from unittest.mock import MagicMock

import pygame
import pytest

# Em execuções completas do pytest, outro teste pode deixar um módulo fake em
# sys.modules. Se `engine.physics` não tiver __path__, ele não é pacote real e
# quebra imports como `engine.physics.collider`.
physics_module = sys.modules.get("engine.physics")
if physics_module is not None and not hasattr(physics_module, "__path__"):
    sys.modules.pop("engine.physics", None)
sys.modules.pop("engine.physics.collider", None)

pygame.init()

from engine.physics.collider import BoxCollider, CircleCollider, CollisionInfo


class _FakeRigidBody:
    def __init__(self, vx: float = 0.0, vy: float = 0.0, kinematic: bool = False):
        self.velocity = [vx, vy]
        self.is_kinematic = kinematic


def _make_transform(x: float = 0.0, y: float = 0.0):
    transform = MagicMock()
    transform.position = [x, y]
    transform.get_world_position.return_value = [x, y]
    return transform


def _make_go(x: float = 0.0, y: float = 0.0, active: bool = True, scene=None, rb=None):
    go = MagicMock()
    go.active = active
    go.scene = scene if scene is not None else MagicMock()
    go.transform = _make_transform(x, y)

    def _get_component(cls):
        from engine.physics.rigidbody import RigidBody

        if cls is RigidBody:
            return rb
        return None

    go.get_component.side_effect = _get_component
    return go


def _box(
    x: float = 0.0,
    y: float = 0.0,
    w: float = 32.0,
    h: float = 32.0,
    ox: float = 0.0,
    oy: float = 0.0,
    trigger: bool = False,
    rb=None,
    scene=None,
    active: bool = True,
) -> BoxCollider:
    collider = BoxCollider(width=w, height=h, offset_x=ox, offset_y=oy, is_trigger=trigger)
    collider.game_object = _make_go(x, y, active=active, rb=rb, scene=scene)
    return collider


def _circle(
    x: float = 0.0,
    y: float = 0.0,
    r: float = 16.0,
    ox: float = 0.0,
    oy: float = 0.0,
    trigger: bool = False,
    rb=None,
    scene=None,
    active: bool = True,
) -> CircleCollider:
    collider = CircleCollider(radius=r, offset_x=ox, offset_y=oy, is_trigger=trigger)
    collider.game_object = _make_go(x, y, active=active, rb=rb, scene=scene)
    return collider


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


class TestCollisionInfo:
    def test_fields_and_defaults(self):
        other = object()
        info = CollisionInfo(other=other, overlap_x=5.0, overlap_y=3.0)
        assert dataclasses.is_dataclass(CollisionInfo)
        assert info.other is other
        assert info.overlap_x == pytest.approx(5.0)
        assert info.overlap_y == pytest.approx(3.0)

        default_info = CollisionInfo(other=other)
        assert default_info.overlap_x == 0.0
        assert default_info.overlap_y == 0.0


class TestBoxCollider:
    def test_init_defaults_and_custom_values(self):
        default = BoxCollider()
        assert default.width == 32.0
        assert default.height == 32.0
        assert default.offset_x == 0.0
        assert default.offset_y == 0.0
        assert default.is_trigger is False
        assert default.on_collision_enter is None
        assert default.on_collision_exit is None

        custom = BoxCollider(width=64.0, height=48.0, offset_x=10.0, offset_y=-5.0, is_trigger=True)
        assert custom.width == 64.0
        assert custom.height == 48.0
        assert custom.offset_x == 10.0
        assert custom.offset_y == -5.0
        assert custom.is_trigger is True

    def test_lifecycle_registry(self):
        collider = BoxCollider()
        collider.start()
        collider.start()
        assert BoxCollider._registry.count(collider) == 2
        collider.destroy()
        assert collider in BoxCollider._registry
        collider.destroy()
        assert collider not in BoxCollider._registry

    def test_rect_without_game_object(self):
        collider = BoxCollider(width=32, height=32)
        rect = collider.rect
        assert isinstance(rect, pygame.Rect)
        assert rect.topleft == (0, 0)
        assert rect.size == (32, 32)

    def test_rect_with_transform_and_offset(self):
        collider = _box(x=100, y=80, w=40, h=20, ox=10, oy=-5)
        assert collider.rect == pygame.Rect(90, 65, 40, 20)

        collider.game_object.transform.get_world_position.return_value = [70, 70]
        assert collider.rect.topleft == (60, 55)

    def test_collision_enter_only_once_and_exit(self):
        scene = MagicMock()
        a = _box(0, 0, w=20, h=20, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        a.on_collision_enter = MagicMock()
        a.on_collision_exit = MagicMock()
        b.on_collision_enter = MagicMock()
        b.on_collision_exit = MagicMock()
        BoxCollider._registry.extend([a, b])

        BoxCollider.check_all()
        BoxCollider.check_all()
        a.on_collision_enter.assert_called_once()
        b.on_collision_enter.assert_called_once()
        info = a.on_collision_enter.call_args.args[0]
        assert isinstance(info, CollisionInfo)
        assert info.other is b

        b.game_object.transform.get_world_position.return_value = [100, 0]
        BoxCollider.check_all()
        a.on_collision_exit.assert_called_once_with(b)
        b.on_collision_exit.assert_called_once_with(a)

    def test_inactive_different_or_missing_scene_ignored(self):
        scene = MagicMock()
        active = _box(0, 0, scene=scene)
        inactive = _box(0, 0, scene=scene, active=False)
        active.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([active, inactive])
        BoxCollider.check_all()
        active.on_collision_enter.assert_not_called()

        BoxCollider._registry.clear()
        a = _box(0, 0, scene=MagicMock())
        b = _box(0, 0, scene=MagicMock())
        a.on_collision_enter = MagicMock()
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        a.on_collision_enter.assert_not_called()

        BoxCollider._registry.clear()
        a.game_object.scene = None
        b.game_object.scene = None
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()

    def test_orphan_purged_every_60_checks(self):
        collider = BoxCollider()
        collider.game_object = None
        BoxCollider._registry.append(collider)
        for _ in range(60):
            BoxCollider.check_all()
        assert collider not in BoxCollider._registry

    def test_trigger_detects_but_does_not_resolve(self):
        scene = MagicMock()
        rb = _FakeRigidBody()
        a = _box(0, 0, w=20, h=20, trigger=True, rb=rb, scene=scene)
        b = _box(10, 0, w=20, h=20, scene=scene)
        original_position = list(a.game_object.transform.position)
        BoxCollider._registry.extend([a, b])
        BoxCollider.check_all()
        assert b in a._colliding_with
        assert a.game_object.transform.position == original_position

    def test_resolve_dynamic_a_only_x(self):
        rb = _FakeRigidBody(vx=5)
        a = _box(0, 0, rb=rb)
        b = _box(10, 0)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position[0] < 0
        assert rb.velocity[0] == 0

    def test_resolve_both_dynamic_share(self):
        rb_a = _FakeRigidBody(vx=5)
        rb_b = _FakeRigidBody(vx=-5)
        a = _box(0, 0, rb=rb_a)
        b = _box(10, 0, rb=rb_b)
        BoxCollider._resolve(a, b, 10, 20)
        assert a.game_object.transform.position[0] == pytest.approx(-5)
        assert b.game_object.transform.position[0] == pytest.approx(15)

    def test_resolve_y_axis_and_kinematic(self):
        rb = _FakeRigidBody(vy=5)
        a = _box(0, 0, rb=rb)
        b = _box(0, 10)
        BoxCollider._resolve(a, b, 20, 10)
        assert a.game_object.transform.position[1] < 0
        assert rb.velocity[1] == 0

        kinematic = _FakeRigidBody(vx=5, kinematic=True)
        c = _box(0, 0, rb=kinematic)
        d = _box(10, 0)
        BoxCollider._resolve(c, d, 10, 20)
        assert c.game_object.transform.position == [0, 0]


class TestCircleCollider:
    def test_init_and_center(self):
        default = CircleCollider()
        assert default.radius == 16.0
        assert default.offset_x == 0.0
        assert default.offset_y == 0.0
        assert default.is_trigger is False

        without_go = CircleCollider(offset_x=2, offset_y=3)
        assert without_go.center == (2, 3)

        with_go = _circle(10, 20, ox=2, oy=-3)
        assert with_go.center == (12.0, 17.0)

    def test_lifecycle_registry(self):
        collider = CircleCollider()
        collider.start()
        assert collider in CircleCollider._registry
        collider.destroy()
        assert collider not in CircleCollider._registry

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
        rb = _FakeRigidBody()
        a = _circle(0, 0, r=10, trigger=True, rb=rb, scene=scene)
        b = _circle(15, 0, r=10, scene=scene)
        original_position = list(a.game_object.transform.position)
        CircleCollider._registry.extend([a, b])
        CircleCollider.check_all()
        assert b in a._colliding_with
        assert a.game_object.transform.position == original_position

    def test_resolve_dist_zero_fallback(self):
        rb = _FakeRigidBody(vx=5)
        a = _circle(0, 0, r=10, rb=rb)
        b = _circle(0, 0, r=10)
        CircleCollider._resolve(a, b, 0, 0, 0, 0, 0, 20)
        assert a.game_object.transform.position[0] < 0
        assert rb.velocity[0] == 0
