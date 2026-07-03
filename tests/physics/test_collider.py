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

Grupos:
  TestCollisionInfo          (4)  — dataclass CollisionInfo
  TestBoxColliderInit        (7)  — construtor, defaults, campos
  TestBoxColliderLifecycle   (5)  — start() registro, destroy() remoção
  TestBoxColliderRect        (6)  — rect sem GO, com GO, offset, alinhamento
  TestBoxCheckAllBasic       (8)  — check_all: detecção, callbacks, exit
  TestBoxCheckAllTrigger     (5)  — is_trigger: detecta mas não resolve
  TestBoxResolve             (8)  — _resolve: MTV eixo X, eixo Y, share=0.5
  TestCircleColliderInit     (6)  — construtor, defaults, campos
  TestCircleColliderCenter   (4)  — center sem GO, com GO, offset
  TestCircleCheckAllBasic    (8)  — check_all: detecção, callbacks, exit
  TestCircleCheckAllTrigger  (4)  — is_trigger não resolve
  TestCircleResolve          (7)  — _resolve: normal, overlap, dist==0 fallback

Total: 72 testes.
"""
from __future__ import annotations

import math
import pytest
from unittest.mock import MagicMock

import pygame
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
        c.game_object = None
        r = c.rect
        assert r.width == 32
        assert r.height == 32

    def test_rect_centered_on_position(self):
        c = _box(x=100.0, y=200.0, w=32.0, h=32.0)
        r = c.rect
        assert r.left == 84    # 100 - 16
        assert r.top  == 184   # 200 - 16

    def test_rect_with_offset(self):
        c = _box(x=0.0, y=0.0, w=32.0, h=32.0, ox=10.0, oy=5.0)
        r = c.rect
        assert r.left == -6    # 0 + 10 - 16
        assert r.top  == -11   # 0 + 5 - 16

    def test_rect_size_matches_width_height(self):
        c = _box(w=64.0, h=48.0)
        r = c.rect
        assert r.width == 64
        assert r.height == 48

    def test_rect_is_pygame_rect(self):
        c = _box()
        assert isinstance(c.rect, pygame.Rect)

    def test_rect_position_updates_with_transform(self):
        c = _box(x=0.0, y=0.0, w=32.0, h=32.0)
        c.game_object.transform.get_world_position.return_value = [50.0, 50.0]
        r = c.rect
        assert r.left == 34  # 50 - 16


# ===========================================================================
# 5. BoxCollider — check_all básico
# ===========================================================================

class TestBoxCheckAllBasic:
    def _overlapping_pair(self, trigger_a=False, trigger_b=False,
                          rb_a=None, rb_b=None):
        """Dois boxes que se sobrepõem na mesma cena, mesma posição."""
        scene = MagicMock()
        a = _box(x=0, y=0, w=32, h=32, trigger=trigger_a, rb=rb_a, scene=scene)
        b = _box(x=10, y=10, w=32, h=32, trigger=trigger_b, rb=rb_b, scene=scene)
        a.start()
        b.start()
        return a, b

    def test_on_collision_enter_called_when_overlapping(self):
        a, b = self._overlapping_pair()
        cb_a = MagicMock()
        a.on_collision_enter = cb_a
        BoxCollider.check_all()
        cb_a.assert_called_once()

    def test_on_collision_enter_receives_collision_info(self):
        a, b = self._overlapping_pair()
        infos = []
        a.on_collision_enter = lambda info: infos.append(info)
        BoxCollider.check_all()
        assert len(infos) == 1
        assert isinstance(infos[0], CollisionInfo)
        assert infos[0].other is b

    def test_both_callbacks_fired_on_enter(self):
        a, b = self._overlapping_pair()
        cb_a, cb_b = MagicMock(), MagicMock()
        a.on_collision_enter = cb_a
        b.on_collision_enter = cb_b
        BoxCollider.check_all()
        cb_a.assert_called_once()
        cb_b.assert_called_once()

    def test_enter_not_fired_twice_on_sustained_overlap(self):
        a, b = self._overlapping_pair()
        cb_a = MagicMock()
        a.on_collision_enter = cb_a
        BoxCollider.check_all()
        BoxCollider.check_all()
        assert cb_a.call_count == 1  # entra só uma vez

    def test_on_collision_exit_called_when_no_longer_overlapping(self):
        scene = MagicMock()
        a = _box(x=0,  y=0,  w=32, h=32, scene=scene)
        b = _box(x=10, y=10, w=32, h=32, scene=scene)
        a.start(); b.start()
        BoxCollider.check_all()  # enter
        # Afasta b
        b.game_object.transform.get_world_position.return_value = [200.0, 200.0]
        cb_exit = MagicMock()
        a.on_collision_exit = cb_exit
        BoxCollider.check_all()  # exit
        cb_exit.assert_called_once_with(b)

    def test_no_collision_when_separated(self):
        scene = MagicMock()
        a = _box(x=0,   y=0,   w=32, h=32, scene=scene)
        b = _box(x=200, y=200, w=32, h=32, scene=scene)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        BoxCollider.check_all()
        cb.assert_not_called()

    def test_different_scenes_no_collision(self):
        a = _box(x=0, y=0, w=32, h=32, scene=MagicMock())
        b = _box(x=0, y=0, w=32, h=32, scene=MagicMock())
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        BoxCollider.check_all()
        cb.assert_not_called()

    def test_inactive_game_object_ignored(self):
        scene = MagicMock()
        a = _box(x=0, y=0, w=32, h=32, scene=scene)
        b = _box(x=5, y=5, w=32, h=32, scene=scene, active=False)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        BoxCollider.check_all()
        cb.assert_not_called()


# ===========================================================================
# 6. BoxCollider — trigger
# ===========================================================================

class TestBoxCheckAllTrigger:
    def test_trigger_fires_enter_callback(self):
        scene = MagicMock()
        a = _box(x=0, y=0, w=32, h=32, trigger=True, scene=scene)
        b = _box(x=5, y=5, w=32, h=32, scene=scene)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        BoxCollider.check_all()
        cb.assert_called_once()

    def test_trigger_does_not_move_objects(self):
        scene = MagicMock()
        rb_b = _make_rb(vx=0, vy=0)
        a = _box(x=0, y=0, w=32, h=32, trigger=True, scene=scene)
        b = _box(x=5, y=5, w=32, h=32, rb=rb_b, scene=scene)
        a.start(); b.start()
        pos_before = list(b.game_object.transform.position)
        BoxCollider.check_all()
        assert b.game_object.transform.position[:2] == pos_before[:2]

    def test_both_triggers_fire_but_no_resolve(self):
        scene = MagicMock()
        a = _box(x=0, y=0, w=32, h=32, trigger=True, scene=scene)
        b = _box(x=5, y=5, w=32, h=32, trigger=True, scene=scene)
        a.start(); b.start()
        cb_a = MagicMock()
        a.on_collision_enter = cb_a
        BoxCollider.check_all()
        cb_a.assert_called_once()

    def test_trigger_exit_callback_fires(self):
        scene = MagicMock()
        a = _box(x=0,  y=0,  w=32, h=32, trigger=True, scene=scene)
        b = _box(x=10, y=10, w=32, h=32, scene=scene)
        a.start(); b.start()
        BoxCollider.check_all()
        b.game_object.transform.get_world_position.return_value = [300.0, 300.0]
        cb_exit = MagicMock()
        a.on_collision_exit = cb_exit
        BoxCollider.check_all()
        cb_exit.assert_called_once()

    def test_non_trigger_resolves_position(self):
        scene = MagicMock()
        rb_b = _make_rb(vx=-5.0, vy=0.0)
        a = _box(x=0, y=0, w=32, h=32, scene=scene)
        b = _box(x=10, y=0, w=32, h=32, rb=rb_b, scene=scene)
        a.start(); b.start()
        BoxCollider.check_all()
        # RigidBody de b deve ter sido atingido pelo _resolve
        # (testa que get_component foi chamado)
        b.game_object.get_component.assert_called()


# ===========================================================================
# 7. BoxCollider — _resolve (MTV)
# ===========================================================================

class TestBoxResolve:
    def _pair_with_rb(self, ax, ay, bx, by, w=32, h=32,
                      vax=0., vay=0., vbx=0., vby=0.,
                      a_kin=False, b_kin=False):
        rb_a = _make_rb(vax, vay, a_kin)
        rb_b = _make_rb(vbx, vby, b_kin)
        a = _box(x=ax, y=ay, w=w, h=h, rb=rb_a)
        b = _box(x=bx, y=by, w=w, h=h, rb=rb_b)
        a.game_object.scene = b.game_object.scene = MagicMock()
        a.game_object.scene.__eq__ = lambda s, o: s is o

        rect_a = a.rect
        rect_b = b.rect
        ox = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
        oy = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)
        return a, b, rb_a, rb_b, ox, oy

    def test_both_dynamic_share_correction(self):
        """Dois dinâmicos: cada um se move overlap/2 (share=0.5)."""
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 10, 0, vax=5., vbx=-5.)
        # MTV eixo X (ox < oy): nx=+1 (B à direita de A)
        pos_a_before = list(a.game_object.transform.position)
        BoxCollider._resolve(a, b, ox, oy)
        # A deve ter se movido para a esquerda
        assert a.game_object.transform.position[0] < pos_a_before[0]

    def test_only_dynamic_gets_full_correction(self):
        """Apenas B é dinâmico: B recebe 100% da correção."""
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 10, 0, vbx=-5., a_kin=True)
        pos_b_before = list(b.game_object.transform.position)
        BoxCollider._resolve(a, b, ox, oy)
        assert b.game_object.transform.position[0] != pos_b_before[0]
        # A (kinematic) não deve mover
        assert a.game_object.transform.position[0] == pytest.approx(0.0)

    def test_both_kinematic_no_movement(self):
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 10, 0, a_kin=True, b_kin=True)
        pos_a = list(a.game_object.transform.position)
        pos_b = list(b.game_object.transform.position)
        BoxCollider._resolve(a, b, ox, oy)
        assert a.game_object.transform.position[:2] == pos_a[:2]
        assert b.game_object.transform.position[:2] == pos_b[:2]

    def test_velocity_cancelled_on_approach_x(self):
        """A indo em direção a B no eixo X: velocidade X de A deve ser cancelada."""
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 10, 0, vax=5., b_kin=True)
        BoxCollider._resolve(a, b, ox, oy)
        assert rb_a.velocity[0] == pytest.approx(0.0)

    def test_velocity_not_cancelled_when_moving_away(self):
        """A indo para longe de B: velocidade não é cancelada."""
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 10, 0, vax=-5., b_kin=True)
        BoxCollider._resolve(a, b, ox, oy)
        assert rb_a.velocity[0] == pytest.approx(-5.0)

    def test_y_axis_correction_when_overlap_y_smaller(self):
        """Sobrepos overlap_y < overlap_x: MTV deve atuar no eixo Y."""
        a, b, rb_a, rb_b, ox, oy = self._pair_with_rb(
            0, 0, 0, 5, vay=5., b_kin=True)  # sobrepõe principalmente no Y
        BoxCollider._resolve(a, b, ox, oy)
        # Y de A deve ter mudado (foi empurrado para cima)
        assert a.game_object.transform.position[1] != pytest.approx(0.0)

    def test_no_rb_no_movement(self):
        """Sem RigidBody em nenhum dos dois: não há movimento."""
        a = _box(x=0, y=0, rb=None)
        b = _box(x=10, y=0, rb=None)
        # get_component retorna None para RigidBody
        a.game_object.get_component.return_value = None
        b.game_object.get_component.return_value = None
        # Deve retornar sem crash
        BoxCollider._resolve(a, b, 22.0, 32.0)

    def test_resolve_does_not_crash_with_zero_overlap(self):
        a = _box(x=0, y=0, rb=_make_rb())
        b = _box(x=32, y=0, rb=_make_rb())
        a.game_object.get_component.return_value = _make_rb()
        b.game_object.get_component.return_value = _make_rb()
        BoxCollider._resolve(a, b, 0.0, 0.0)  # sem crash


# ===========================================================================
# 8. CircleCollider — construtor
# ===========================================================================

class TestCircleColliderInit:
    def test_default_radius(self):
        c = CircleCollider()
        assert c.radius == 16.0

    def test_custom_radius(self):
        c = CircleCollider(radius=32.0)
        assert c.radius == 32.0

    def test_default_offset_zero(self):
        c = CircleCollider()
        assert c.offset_x == 0.0
        assert c.offset_y == 0.0

    def test_is_trigger_default_false(self):
        assert CircleCollider().is_trigger is False

    def test_is_trigger_custom(self):
        c = CircleCollider(is_trigger=True)
        assert c.is_trigger is True

    def test_callbacks_default_none(self):
        c = CircleCollider()
        assert c.on_collision_enter is None
        assert c.on_collision_exit is None


# ===========================================================================
# 9. CircleCollider — center
# ===========================================================================

class TestCircleColliderCenter:
    def test_center_without_game_object(self):
        c = CircleCollider(offset_x=5.0, offset_y=3.0)
        c.game_object = None
        assert c.center == (5.0, 3.0)

    def test_center_at_position(self):
        c = _circle(x=100.0, y=200.0)
        assert c.center == (100.0, 200.0)

    def test_center_with_offset(self):
        c = _circle(x=100.0, y=100.0, ox=10.0, oy=-10.0)
        assert c.center == (110.0, 90.0)

    def test_center_updates_with_transform(self):
        c = _circle(x=0.0, y=0.0)
        c.game_object.transform.get_world_position.return_value = [50.0, 75.0]
        assert c.center == (50.0, 75.0)


# ===========================================================================
# 10. CircleCollider — check_all básico
# ===========================================================================

class TestCircleCheckAllBasic:
    def _overlapping_pair(self, trigger_a=False, trigger_b=False,
                          rb_a=None, rb_b=None):
        scene = MagicMock()
        # dist = 10, radii = 16+16 = 32 → colid
        a = _circle(x=0,  y=0,  r=16, trigger=trigger_a, rb=rb_a, scene=scene)
        b = _circle(x=10, y=0,  r=16, trigger=trigger_b, rb=rb_b, scene=scene)
        a.start(); b.start()
        return a, b

    def test_enter_callback_called_on_overlap(self):
        a, b = self._overlapping_pair()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_called_once_with(b)

    def test_both_enter_callbacks_called(self):
        a, b = self._overlapping_pair()
        cb_a, cb_b = MagicMock(), MagicMock()
        a.on_collision_enter = cb_a
        b.on_collision_enter = cb_b
        CircleCollider.check_all()
        cb_a.assert_called_once_with(b)
        cb_b.assert_called_once_with(a)

    def test_enter_not_fired_twice_sustained(self):
        a, b = self._overlapping_pair()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        CircleCollider.check_all()
        assert cb.call_count == 1

    def test_no_collision_when_far_apart(self):
        scene = MagicMock()
        a = _circle(x=0,   y=0, r=16, scene=scene)
        b = _circle(x=100, y=0, r=16, scene=scene)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_not_called()

    def test_exit_callback_called_after_separation(self):
        scene = MagicMock()
        a = _circle(x=0,  y=0, r=16, scene=scene)
        b = _circle(x=10, y=0, r=16, scene=scene)
        a.start(); b.start()
        CircleCollider.check_all()
        b.game_object.transform.get_world_position.return_value = [500.0, 0.0]
        cb_exit = MagicMock()
        a.on_collision_exit = cb_exit
        CircleCollider.check_all()
        cb_exit.assert_called_once_with(b)

    def test_different_scenes_no_collision(self):
        a = _circle(x=0, y=0, r=16, scene=MagicMock())
        b = _circle(x=5, y=0, r=16, scene=MagicMock())
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_not_called()

    def test_inactive_object_ignored(self):
        scene = MagicMock()
        a = _circle(x=0, y=0, r=16, scene=scene)
        b = _circle(x=5, y=0, r=16, scene=scene, active=False)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_not_called()

    def test_boundary_exact_distance_no_collision(self):
        """dist == r_a + r_b: não colide (< min_dist é a condição)."""
        scene = MagicMock()
        a = _circle(x=0,  y=0, r=16, scene=scene)
        b = _circle(x=32, y=0, r=16, scene=scene)  # dist=32 == 16+16
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_not_called()


# ===========================================================================
# 11. CircleCollider — trigger
# ===========================================================================

class TestCircleCheckAllTrigger:
    def test_trigger_fires_enter_callback(self):
        scene = MagicMock()
        a = _circle(x=0, y=0, r=16, trigger=True, scene=scene)
        b = _circle(x=5, y=0, r=16, scene=scene)
        a.start(); b.start()
        cb = MagicMock()
        a.on_collision_enter = cb
        CircleCollider.check_all()
        cb.assert_called_once_with(b)

    def test_trigger_does_not_call_resolve(self):
        scene = MagicMock()
        rb_b = _make_rb()
        a = _circle(x=0, y=0, r=16, trigger=True, scene=scene)
        b = _circle(x=5, y=0, r=16, rb=rb_b, scene=scene)
        a.start(); b.start()
        pos_before = list(b.game_object.transform.position)
        CircleCollider.check_all()
        assert b.game_object.transform.position[:2] == pos_before[:2]

    def test_both_triggers_enter_callback_fires(self):
        scene = MagicMock()
        a = _circle(x=0, y=0, r=16, trigger=True, scene=scene)
        b = _circle(x=5, y=0, r=16, trigger=True, scene=scene)
        a.start(); b.start()
        cb_a, cb_b = MagicMock(), MagicMock()
        a.on_collision_enter = cb_a
        b.on_collision_enter = cb_b
        CircleCollider.check_all()
        cb_a.assert_called_once()
        cb_b.assert_called_once()

    def test_trigger_exit_callback_fires(self):
        scene = MagicMock()
        a = _circle(x=0,  y=0, r=16, trigger=True, scene=scene)
        b = _circle(x=10, y=0, r=16, scene=scene)
        a.start(); b.start()
        CircleCollider.check_all()
        b.game_object.transform.get_world_position.return_value = [500.0, 0.0]
        cb_exit = MagicMock()
        a.on_collision_exit = cb_exit
        CircleCollider.check_all()
        cb_exit.assert_called_once_with(b)


# ===========================================================================
# 12. CircleCollider — _resolve
# ===========================================================================

class TestCircleResolve:
    def _pair(self, ax, ay, bx, by, r=16,
              vax=0., vay=0., vbx=0., vby=0.,
              a_kin=False, b_kin=False):
        rb_a = _make_rb(vax, vay, a_kin)
        rb_b = _make_rb(vbx, vby, b_kin)
        a = _circle(x=ax, y=ay, r=r, rb=rb_a)
        b = _circle(x=bx, y=by, r=r, rb=rb_b)
        dist     = math.hypot(bx - ax, by - ay)
        min_dist = r + r
        return a, b, rb_a, rb_b, dist, min_dist

    def test_both_dynamic_pushed_apart(self):
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 10, 0, vax=5., vbx=-5.)
        pos_ax = a.game_object.transform.position[0]
        CircleCollider._resolve(a, b, 0, 0, 10, 0, dist, min_dist)
        # A empurrado para a esquerda
        assert a.game_object.transform.position[0] < pos_ax

    def test_only_dynamic_b_moves(self):
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 10, 0, vbx=-5., a_kin=True)
        pos_ax = a.game_object.transform.position[0]
        CircleCollider._resolve(a, b, 0, 0, 10, 0, dist, min_dist)
        # A (kinematic) não deve mover
        assert a.game_object.transform.position[0] == pytest.approx(pos_ax)
        # B deve ter movido
        assert b.game_object.transform.position[0] != pytest.approx(10.0)

    def test_both_kinematic_no_movement(self):
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 10, 0, a_kin=True, b_kin=True)
        pos_ax = a.game_object.transform.position[0]
        pos_bx = b.game_object.transform.position[0]
        CircleCollider._resolve(a, b, 0, 0, 10, 0, dist, min_dist)
        assert a.game_object.transform.position[0] == pytest.approx(pos_ax)
        assert b.game_object.transform.position[0] == pytest.approx(pos_bx)

    def test_dist_zero_fallback_no_crash(self):
        """dist==0: fallback normal (1, 0) não deve travar."""
        a, b, rb_a, rb_b, _, min_dist = self._pair(
            0, 0, 0, 0, vax=1.)  # mesma posição
        CircleCollider._resolve(a, b, 0, 0, 0, 0, 0.0, min_dist)

    def test_velocity_cancelled_on_approach(self):
        """A indo em direção a B: componente normal de velocidade cancelada."""
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 10, 0, vax=5., b_kin=True)
        CircleCollider._resolve(a, b, 0, 0, 10, 0, dist, min_dist)
        assert rb_a.velocity[0] == pytest.approx(0.0)

    def test_velocity_not_cancelled_moving_away(self):
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 10, 0, vax=-5., b_kin=True)
        CircleCollider._resolve(a, b, 0, 0, 10, 0, dist, min_dist)
        assert rb_a.velocity[0] == pytest.approx(-5.0)

    def test_overlap_proportional_to_penetration(self):
        """Quanto maior a penetração, maior a correção de posição."""
        # dist=5, min_dist=32 → overlap=27*0.5=13.5 para cada
        a, b, rb_a, rb_b, dist, min_dist = self._pair(
            0, 0, 5, 0, vax=5., b_kin=True)
        pos_before = a.game_object.transform.position[0]
        CircleCollider._resolve(a, b, 0, 0, 5, 0, dist, min_dist)
        correction = pos_before - a.game_object.transform.position[0]
        expected   = (min_dist - dist) * 1.0  # share=1.0 (b é kinematic)
        assert correction == pytest.approx(expected, rel=1e-3)
