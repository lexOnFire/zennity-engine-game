"""
tests/core/test_component.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/core/component.py.

Estratégia:
  - Sem pygame, sem Scene: Component e Transform são puro Python + numpy.
  - engine.graphics.math3d é mockado onde necessário (get_model_matrix)
    para evitar importar OpenGL/pygame em contexto de teste puro.
  - Cada teste cria seus próprios objetos — sem estado compartilhado.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest

# ── stub mínimo de math3d (evita importar OpenGL) ───────────────────────────
_math3d = ModuleType("engine.graphics.math3d")
_math3d.translation_matrix = lambda x, y, z: np.eye(4, dtype=np.float32)
_math3d.rotation_matrix    = lambda rx, ry, rz: np.eye(4, dtype=np.float32)
_math3d.scale_matrix       = lambda sx, sy, sz: np.eye(4, dtype=np.float32)
sys.modules.setdefault("engine.graphics.math3d", _math3d)

from engine.core.component import Component, Transform  # noqa: E402
from engine.game_object import GameObject               # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
class TestComponentInit:
    def test_game_object_none_by_default(self):
        assert Component().game_object is None

    def test_started_false_by_default(self):
        assert Component()._started is False

    def test_repr_detached(self):
        assert "<detached>" in repr(Component())

    def test_repr_with_game_object(self):
        go   = GameObject()
        comp = Component()
        go.add_component(comp)
        assert go.name in repr(comp)

    def test_repr_shows_started_state(self):
        comp = Component()
        assert "started=False" in repr(comp)


# ─────────────────────────────────────────────────────────────────────────────
class TestComponentLifecycle:
    def test_start_is_noop_by_default(self):
        comp = Component()
        comp.start()  # não deve lançar

    def test_update_is_noop_by_default(self):
        comp = Component()
        comp.update(0.016)  # não deve lançar

    def test_draw_is_noop_by_default(self):
        comp = Component()
        comp.draw(MagicMock())  # não deve lançar

    def test_destroy_is_noop_by_default(self):
        comp = Component()
        comp.destroy()  # não deve lançar

    def test_subclass_can_override_start(self):
        called = []
        class MyComp(Component):
            def start(self): called.append(True)
        go = GameObject()
        comp = MyComp()
        go.add_component(comp)
        go._scene = MagicMock()   # simula cena para disparar start
        # re-add para disparar o caminho com scene
        go.remove_component(comp)
        comp._started = False
        go.add_component(comp)    # com _scene setado, start() é chamado
        assert called == [True]

    def test_subclass_update_receives_dt(self):
        received = []
        class MyComp(Component):
            def update(self, dt): received.append(dt)
        go   = GameObject()
        comp = MyComp()
        go.add_component(comp)
        go.update(0.032)
        assert received == [0.032]


# ─────────────────────────────────────────────────────────────────────────────
class TestComponentProperties:
    def test_transform_property_returns_go_transform(self):
        go   = GameObject()
        comp = Component()
        go.add_component(comp)
        assert comp.transform is go.transform

    def test_transform_property_raises_when_detached(self):
        comp = Component()
        with pytest.raises(AssertionError):
            _ = comp.transform

    def test_scene_property_returns_none_when_detached(self):
        assert Component().scene is None

    def test_scene_property_delegates_to_game_object(self):
        go        = GameObject()
        go._scene = MagicMock()
        comp      = Component()
        go.add_component(comp)
        assert comp.scene is go._scene


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformInit:
    def test_default_position_zero(self):
        t = Transform()
        assert t.x == pytest.approx(0.0)
        assert t.y == pytest.approx(0.0)
        assert t.z == pytest.approx(0.0)

    def test_default_rotation_zero(self):
        t = Transform()
        assert t.rx == pytest.approx(0.0)
        assert t.ry == pytest.approx(0.0)
        assert t.rz == pytest.approx(0.0)

    def test_default_scale_one(self):
        t = Transform()
        assert t.sx == pytest.approx(1.0)
        assert t.sy == pytest.approx(1.0)
        assert t.sz == pytest.approx(1.0)

    def test_custom_init_values(self):
        t = Transform(x=3.0, y=-2.0, rz=45.0, sx=2.0)
        assert t.x  == pytest.approx(3.0)
        assert t.y  == pytest.approx(-2.0)
        assert t.rz == pytest.approx(45.0)
        assert t.sx == pytest.approx(2.0)

    def test_position_array_dtype_float32(self):
        assert Transform()._position.dtype == np.float32

    def test_rotation_array_dtype_float32(self):
        assert Transform()._rotation.dtype == np.float32

    def test_scale_array_dtype_float32(self):
        assert Transform()._scale.dtype == np.float32


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformSetters:
    def test_set_x(self):
        t = Transform()
        t.x = 5.0
        assert t.x == pytest.approx(5.0)

    def test_set_y(self):
        t = Transform()
        t.y = -3.5
        assert t.y == pytest.approx(-3.5)

    def test_set_z(self):
        t = Transform()
        t.z = 1.0
        assert t.z == pytest.approx(1.0)

    def test_set_rx(self):
        t = Transform()
        t.rx = 90.0
        assert t.rx == pytest.approx(90.0)

    def test_set_ry(self):
        t = Transform()
        t.ry = 180.0
        assert t.ry == pytest.approx(180.0)

    def test_set_rz(self):
        t = Transform()
        t.rz = -45.0
        assert t.rz == pytest.approx(-45.0)

    def test_set_sx(self):
        t = Transform()
        t.sx = 3.0
        assert t.sx == pytest.approx(3.0)

    def test_set_sy(self):
        t = Transform()
        t.sy = 0.5
        assert t.sy == pytest.approx(0.5)

    def test_set_sz(self):
        t = Transform()
        t.sz = 2.0
        assert t.sz == pytest.approx(2.0)

    def test_set_position_array(self):
        t = Transform()
        t.position = [1.0, 2.0, 3.0]
        np.testing.assert_array_almost_equal(t.position, [1.0, 2.0, 3.0])

    def test_set_rotation_array(self):
        t = Transform()
        t.rotation = [10.0, 20.0, 30.0]
        np.testing.assert_array_almost_equal(t.rotation, [10.0, 20.0, 30.0])

    def test_set_scale_array(self):
        t = Transform()
        t.scale = [2.0, 3.0, 4.0]
        np.testing.assert_array_almost_equal(t.scale, [2.0, 3.0, 4.0])


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformTranslate:
    def test_translate_xy(self):
        t = Transform(x=1.0, y=2.0)
        t.translate(3.0, -1.0)
        assert t.x == pytest.approx(4.0)
        assert t.y == pytest.approx(1.0)

    def test_translate_z_default_zero(self):
        t = Transform(z=5.0)
        t.translate(0.0, 0.0)
        assert t.z == pytest.approx(5.0)

    def test_translate_z_explicit(self):
        t = Transform(z=1.0)
        t.translate(0.0, 0.0, 2.0)
        assert t.z == pytest.approx(3.0)

    def test_translate_accumulates(self):
        t = Transform()
        t.translate(1.0, 1.0)
        t.translate(2.0, 3.0)
        assert t.x == pytest.approx(3.0)
        assert t.y == pytest.approx(4.0)

    def test_translate_negative(self):
        t = Transform(x=5.0)
        t.translate(-5.0, 0.0)
        assert t.x == pytest.approx(0.0)


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformRotate:
    def test_rotate_rz(self):
        t = Transform()
        t.rotate(0.0, 0.0, 45.0)
        assert t.rz == pytest.approx(45.0)

    def test_rotate_accumulates(self):
        t = Transform()
        t.rotate(0.0, 0.0, 90.0)
        t.rotate(0.0, 0.0, 90.0)
        assert t.rz == pytest.approx(180.0)

    def test_rotate_all_axes(self):
        t = Transform()
        t.rotate(10.0, 20.0, 30.0)
        assert t.rx == pytest.approx(10.0)
        assert t.ry == pytest.approx(20.0)
        assert t.rz == pytest.approx(30.0)


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformModelMatrix:
    def test_get_model_matrix_returns_4x4(self):
        go = GameObject()
        m  = go.transform.get_model_matrix()
        assert m.shape == (4, 4)

    def test_get_model_matrix_identity_at_origin(self):
        go = GameObject()
        m  = go.transform.get_model_matrix()
        np.testing.assert_array_almost_equal(m, np.eye(4))

    def test_world_position_alias(self):
        go = GameObject()
        np.testing.assert_array_almost_equal(
            go.transform.world_position,
            go.transform.get_world_position()
        )

    def test_world_rotation_no_parent(self):
        go = GameObject()
        go.transform.rotate(0.0, 0.0, 30.0)
        np.testing.assert_array_almost_equal(
            go.transform.world_rotation,
            [0.0, 0.0, 30.0]
        )

    def test_world_rotation_with_parent(self):
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.transform.rotate(0.0, 0.0, 10.0)
        child.transform.rotate(0.0, 0.0, 20.0)
        wr = child.transform.world_rotation
        assert wr[2] == pytest.approx(30.0)


# ─────────────────────────────────────────────────────────────────────────────
class TestTransformRepr:
    def test_repr_detached(self):
        t = Transform()
        assert "<detached>" in repr(t)

    def test_repr_with_game_object(self):
        go = GameObject("Ship")
        assert "Ship" in repr(go.transform)

    def test_repr_shows_position(self):
        go = GameObject()
        go.transform.x = 3.0
        go.transform.y = -1.0
        r  = repr(go.transform)
        assert "3.0" in r
        assert "-1.0" in r

    def test_repr_shows_rotation(self):
        go = GameObject()
        go.transform.rz = 45.0
        assert "45.0" in repr(go.transform)
