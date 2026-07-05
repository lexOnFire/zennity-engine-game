"""
tests/unit/test_transform.py
Testes unitários para o componente Transform.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from engine.game_object import GameObject
from engine.core.component import Transform


@pytest.fixture
def go_with_transform() -> GameObject:
    go = GameObject("T")
    return go


# ── Valores padrão ────────────────────────────────────────────────────────────

def test_transform_default_position(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    assert t.x == pytest.approx(0.0)
    assert t.y == pytest.approx(0.0)
    assert t.z == pytest.approx(0.0)


def test_transform_default_rotation(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    assert t.rx == pytest.approx(0.0)
    assert t.ry == pytest.approx(0.0)
    assert t.rz == pytest.approx(0.0)


def test_transform_default_scale(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    assert t.sx == pytest.approx(1.0)
    assert t.sy == pytest.approx(1.0)
    assert t.sz == pytest.approx(1.0)


# ── Setters de posição ────────────────────────────────────────────────────────

def test_transform_set_x(go_with_transform: GameObject) -> None:
    go_with_transform.transform.x = 100.0
    assert go_with_transform.transform.x == pytest.approx(100.0)


def test_transform_set_y(go_with_transform: GameObject) -> None:
    go_with_transform.transform.y = -50.0
    assert go_with_transform.transform.y == pytest.approx(-50.0)


def test_transform_set_position_array(go_with_transform: GameObject) -> None:
    go_with_transform.transform.position = [10.0, 20.0, 5.0]
    assert go_with_transform.transform.x == pytest.approx(10.0)
    assert go_with_transform.transform.y == pytest.approx(20.0)
    assert go_with_transform.transform.z == pytest.approx(5.0)


# ── Setters de rotação ────────────────────────────────────────────────────────

def test_transform_set_rz(go_with_transform: GameObject) -> None:
    go_with_transform.transform.rz = 45.0
    assert go_with_transform.transform.rz == pytest.approx(45.0)


def test_transform_set_rotation_array(go_with_transform: GameObject) -> None:
    go_with_transform.transform.rotation = [10.0, 20.0, 30.0]
    assert go_with_transform.transform.rx == pytest.approx(10.0)
    assert go_with_transform.transform.ry == pytest.approx(20.0)
    assert go_with_transform.transform.rz == pytest.approx(30.0)


# ── Setters de escala ─────────────────────────────────────────────────────────

def test_transform_set_sx(go_with_transform: GameObject) -> None:
    go_with_transform.transform.sx = 2.5
    assert go_with_transform.transform.sx == pytest.approx(2.5)


def test_transform_set_scale_array(go_with_transform: GameObject) -> None:
    go_with_transform.transform.scale = [2.0, 3.0, 1.0]
    assert go_with_transform.transform.sx == pytest.approx(2.0)
    assert go_with_transform.transform.sy == pytest.approx(3.0)


# ── translate() ───────────────────────────────────────────────────────────────

def test_transform_translate_2d(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    t.x = 10.0
    t.y = 20.0
    t.translate(5.0, -3.0)
    assert t.x == pytest.approx(15.0)
    assert t.y == pytest.approx(17.0)


def test_transform_translate_preserves_z(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    t.z = 100.0
    t.translate(0.0, 0.0)
    assert t.z == pytest.approx(100.0)


# ── rotate() ─────────────────────────────────────────────────────────────────

def test_transform_rotate(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    t.rotate(0.0, 0.0, 90.0)
    assert t.rz == pytest.approx(90.0)


def test_transform_rotate_accumulates(go_with_transform: GameObject) -> None:
    t = go_with_transform.transform
    t.rotate(0.0, 0.0, 45.0)
    t.rotate(0.0, 0.0, 45.0)
    assert t.rz == pytest.approx(90.0)


# ── dtype float32 ─────────────────────────────────────────────────────────────

def test_transform_position_is_float32(go_with_transform: GameObject) -> None:
    assert go_with_transform.transform.position.dtype == np.float32


def test_transform_scale_is_float32(go_with_transform: GameObject) -> None:
    assert go_with_transform.transform.scale.dtype == np.float32


# ── world_position em hierarquia ──────────────────────────────────────────────

def test_world_position_no_parent(go_with_transform: GameObject) -> None:
    go_with_transform.transform.position = [5.0, 10.0, 0.0]
    wp = go_with_transform.transform.world_position
    assert wp[0] == pytest.approx(5.0)
    assert wp[1] == pytest.approx(10.0)


def test_world_position_with_parent() -> None:
    parent = GameObject("Parent")
    child = GameObject("Child")
    parent.transform.position = [100.0, 0.0, 0.0]
    child.transform.position = [10.0, 0.0, 0.0]
    parent.add_child(child)
    wp = child.transform.world_position
    # Filho em (10,0) dentro do pai em (100,0) = world (110, 0)
    assert wp[0] == pytest.approx(110.0, abs=0.01)


# ── repr ──────────────────────────────────────────────────────────────────────

def test_transform_repr_contains_go_name(go_with_transform: GameObject) -> None:
    r = repr(go_with_transform.transform)
    assert "T" in r
