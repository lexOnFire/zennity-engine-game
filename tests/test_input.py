"""
tests/test_input.py
─────────────────────────────────────────────────────────────────
Testes unitários de engine/input.py.

Estratégia de isolamento:
  - pygame é substituido por um stub completo antes de qualquer import
    de engine.input, para que nenhuma inicialização real ocorra.
  - _KeysWrapper imita pygame.key.ScancodeWrapper: suporta indexação
    e avalia como bool(False) quando vazio, exatamente como o original.
  - Cada teste que precise de teclas/mouse configura os atributos de
    classe diretamente em Input, sem precisar de pygame.
  - autouse fixture reseta Input para estado limpo entre testes.
"""
from __future__ import annotations

import sys
import types
from typing import Sequence
from unittest.mock import MagicMock

import pytest


# ─────────────────────────────────────────────────────────────────
# Fake wrapper que imita pygame.key.ScancodeWrapper
# ─────────────────────────────────────────────────────────────────

class _KeysWrapper:
    """
    Imita pygame.key.ScancodeWrapper.
    keys é um dict {key_code: bool} ou uma sequência.
    bool(_KeysWrapper()) é False quando keys está vazio.
    """
    def __init__(self, keys=None):
        self._keys = keys or {}

    def __getitem__(self, key):
        if isinstance(self._keys, dict):
            return self._keys.get(key, False)
        try:
            return self._keys[key]
        except (IndexError, KeyError):
            return False

    def __bool__(self):
        return bool(self._keys)


KEY_LEFT  = 276
KEY_RIGHT = 275
KEY_UP    = 273
KEY_DOWN  = 274
KEY_A     = 97
KEY_D     = 100
KEY_W     = 119
KEY_S     = 115
KEY_SPACE = 32
KEY_Z     = 122


# ─────────────────────────────────────────────────────────────────
# Stub de pygame (antes do import de engine.input)
# ─────────────────────────────────────────────────────────────────

_empty_wrapper = _KeysWrapper()

_pg_key = MagicMock()
_pg_key.ScancodeWrapper = _KeysWrapper
_pg_key.get_pressed     = MagicMock(return_value=_empty_wrapper)
_pg_key.K_LEFT          = KEY_LEFT
_pg_key.K_RIGHT         = KEY_RIGHT
_pg_key.K_UP            = KEY_UP
_pg_key.K_DOWN          = KEY_DOWN
_pg_key.K_a             = KEY_A
_pg_key.K_d             = KEY_D
_pg_key.K_w             = KEY_W
_pg_key.K_s             = KEY_S
_pg_key.K_SPACE         = KEY_SPACE

_pg_mouse = MagicMock()
_pg_mouse.get_pressed = MagicMock(return_value=(False, False, False))
_pg_mouse.get_pos     = MagicMock(return_value=(0, 0))
_pg_mouse.get_rel     = MagicMock(return_value=(0, 0))

_pg_mod = MagicMock()
_pg_mod.key   = _pg_key
_pg_mod.mouse = _pg_mouse
# constantes de tecla usadas em engine/input.py
for _attr, _val in {
    "K_LEFT":  KEY_LEFT,  "K_RIGHT": KEY_RIGHT,
    "K_UP":    KEY_UP,    "K_DOWN":  KEY_DOWN,
    "K_a":     KEY_A,     "K_d":     KEY_D,
    "K_w":     KEY_W,     "K_s":     KEY_S,
    "K_SPACE": KEY_SPACE,
}.items():
    setattr(_pg_mod, _attr, _val)

sys.modules["pygame"]         = _pg_mod
sys.modules["pygame.key"]     = _pg_key
sys.modules["pygame.mouse"]   = _pg_mouse
sys.modules["pygame.mixer"]   = MagicMock()
sys.modules["pygame.display"] = MagicMock()

from engine.input import Input  # noqa: E402


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def keys(*pressed):
    """Cria _KeysWrapper com as teclas fornecidas em estado pressed=True."""
    return _KeysWrapper({k: True for k in pressed})


def no_keys():
    return _KeysWrapper()


@pytest.fixture(autouse=True)
def reset_input():
    """Reseta o estado de Input antes de cada teste."""
    Input._keys_current   = no_keys()
    Input._keys_previous  = no_keys()
    Input._mouse_current  = (False, False, False)
    Input._mouse_previous = (False, False, False)
    Input._mouse_position = (0, 0)
    Input._mouse_rel      = (0, 0)
    yield
    Input._keys_current   = no_keys()
    Input._keys_previous  = no_keys()
    Input._mouse_current  = (False, False, False)
    Input._mouse_previous = (False, False, False)
    Input._mouse_position = (0, 0)
    Input._mouse_rel      = (0, 0)


def press_key(key):
    """Simula uma tecla sendo pressionada: previous=off, current=on."""
    Input._keys_previous = no_keys()
    Input._keys_current  = keys(key)


def hold_key(key):
    """Simula uma tecla sendo mantida: previous=on, current=on."""
    Input._keys_previous = keys(key)
    Input._keys_current  = keys(key)


def release_key(key):
    """Simula soltação de tecla: previous=on, current=off."""
    Input._keys_previous = keys(key)
    Input._keys_current  = no_keys()


# ─────────────────────────────────────────────────────────────────
class TestGetKey:
    def test_held_key_returns_true(self):
        hold_key(KEY_SPACE)
        assert Input.get_key(KEY_SPACE) is True

    def test_unpressed_key_returns_false(self):
        assert Input.get_key(KEY_SPACE) is False

    def test_just_pressed_key_returns_true(self):
        press_key(KEY_SPACE)
        assert Input.get_key(KEY_SPACE) is True

    def test_released_key_returns_false(self):
        release_key(KEY_SPACE)
        assert Input.get_key(KEY_SPACE) is False

    def test_invalid_key_returns_false(self):
        assert Input.get_key(99999) is False

    def test_empty_wrapper_returns_false(self):
        # _keys_current vazio (falsy)
        assert Input.get_key(KEY_A) is False


class TestGetKeyDown:
    def test_just_pressed_returns_true(self):
        press_key(KEY_A)
        assert Input.get_key_down(KEY_A) is True

    def test_held_returns_false(self):
        hold_key(KEY_A)
        assert Input.get_key_down(KEY_A) is False

    def test_released_returns_false(self):
        release_key(KEY_A)
        assert Input.get_key_down(KEY_A) is False

    def test_never_pressed_returns_false(self):
        assert Input.get_key_down(KEY_A) is False

    def test_invalid_key_returns_false(self):
        Input._keys_current  = keys(KEY_A)
        Input._keys_previous = no_keys()
        assert Input.get_key_down(99999) is False

    def test_empty_current_returns_false(self):
        Input._keys_current  = no_keys()
        Input._keys_previous = keys(KEY_A)
        assert Input.get_key_down(KEY_A) is False


class TestGetKeyUp:
    def test_just_released_returns_true(self):
        release_key(KEY_A)
        assert Input.get_key_up(KEY_A) is True

    def test_held_returns_false(self):
        hold_key(KEY_A)
        assert Input.get_key_up(KEY_A) is False

    def test_just_pressed_returns_false(self):
        press_key(KEY_A)
        assert Input.get_key_up(KEY_A) is False

    def test_never_pressed_returns_false(self):
        assert Input.get_key_up(KEY_A) is False

    def test_invalid_key_returns_false(self):
        release_key(KEY_A)
        assert Input.get_key_up(99999) is False

    def test_empty_previous_returns_false(self):
        Input._keys_current  = no_keys()
        Input._keys_previous = no_keys()
        assert Input.get_key_up(KEY_A) is False


class TestMouseButton:
    def test_held_button_returns_true(self):
        Input._mouse_current = (True, False, False)
        assert Input.get_mouse_button(0) is True

    def test_not_pressed_returns_false(self):
        assert Input.get_mouse_button(0) is False

    def test_middle_button(self):
        Input._mouse_current = (False, True, False)
        assert Input.get_mouse_button(1) is True

    def test_right_button(self):
        Input._mouse_current = (False, False, True)
        assert Input.get_mouse_button(2) is True

    def test_invalid_button_returns_false(self):
        assert Input.get_mouse_button(9) is False


class TestMouseButtonDown:
    def test_just_clicked_returns_true(self):
        Input._mouse_previous = (False, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_down(0) is True

    def test_held_returns_false(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_down(0) is False

    def test_released_returns_false(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (False, False, False)
        assert Input.get_mouse_button_down(0) is False

    def test_never_pressed_returns_false(self):
        assert Input.get_mouse_button_down(0) is False

    def test_invalid_button_returns_false(self):
        assert Input.get_mouse_button_down(9) is False


class TestMouseButtonUp:
    def test_just_released_returns_true(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (False, False, False)
        assert Input.get_mouse_button_up(0) is True

    def test_held_returns_false(self):
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_up(0) is False

    def test_just_pressed_returns_false(self):
        Input._mouse_previous = (False, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_up(0) is False

    def test_never_pressed_returns_false(self):
        assert Input.get_mouse_button_up(0) is False

    def test_invalid_button_returns_false(self):
        assert Input.get_mouse_button_up(9) is False


class TestMousePosition:
    def test_returns_tuple(self):
        Input._mouse_position = (320, 240)
        assert Input.get_mouse_position() == (320, 240)

    def test_default_is_zero(self):
        assert Input.get_mouse_position() == (0, 0)


class TestMouseRel:
    def test_returns_rel(self):
        Input._mouse_rel = (5, -3)
        assert Input.get_mouse_rel() == (5, -3)

    def test_default_is_zero(self):
        assert Input.get_mouse_rel() == (0, 0)


class TestAxisHorizontal:
    def test_left_arrow_returns_minus_one(self):
        hold_key(KEY_LEFT)
        assert Input.get_axis_horizontal() == -1.0

    def test_a_key_returns_minus_one(self):
        hold_key(KEY_A)
        assert Input.get_axis_horizontal() == -1.0

    def test_right_arrow_returns_plus_one(self):
        hold_key(KEY_RIGHT)
        assert Input.get_axis_horizontal() == 1.0

    def test_d_key_returns_plus_one(self):
        hold_key(KEY_D)
        assert Input.get_axis_horizontal() == 1.0

    def test_both_directions_cancel_out(self):
        Input._keys_current = keys(KEY_LEFT, KEY_RIGHT)
        assert Input.get_axis_horizontal() == 0.0

    def test_no_key_returns_zero(self):
        assert Input.get_axis_horizontal() == 0.0

    def test_a_and_d_cancel_out(self):
        Input._keys_current = keys(KEY_A, KEY_D)
        assert Input.get_axis_horizontal() == 0.0


class TestAxisVertical:
    def test_up_arrow_returns_minus_one(self):
        hold_key(KEY_UP)
        assert Input.get_axis_vertical() == -1.0

    def test_w_key_returns_minus_one(self):
        hold_key(KEY_W)
        assert Input.get_axis_vertical() == -1.0

    def test_down_arrow_returns_plus_one(self):
        hold_key(KEY_DOWN)
        assert Input.get_axis_vertical() == 1.0

    def test_s_key_returns_plus_one(self):
        hold_key(KEY_S)
        assert Input.get_axis_vertical() == 1.0

    def test_both_directions_cancel_out(self):
        Input._keys_current = keys(KEY_UP, KEY_DOWN)
        assert Input.get_axis_vertical() == 0.0

    def test_no_key_returns_zero(self):
        assert Input.get_axis_vertical() == 0.0

    def test_w_and_s_cancel_out(self):
        Input._keys_current = keys(KEY_W, KEY_S)
        assert Input.get_axis_vertical() == 0.0


class TestUpdate:
    def test_update_advances_key_state(self):
        _pg_key.get_pressed.return_value = keys(KEY_SPACE)
        _pg_mouse.get_pressed.return_value = (False, False, False)
        _pg_mouse.get_pos.return_value     = (100, 200)
        _pg_mouse.get_rel.return_value     = (5, 10)
        Input.update()
        assert Input.get_key(KEY_SPACE) is True
        assert Input.get_mouse_position() == (100, 200)
        assert Input.get_mouse_rel()      == (5, 10)

    def test_update_saves_previous_key_state(self):
        Input._keys_current = keys(KEY_A)
        _pg_key.get_pressed.return_value   = no_keys()
        _pg_mouse.get_pressed.return_value = (False, False, False)
        _pg_mouse.get_pos.return_value     = (0, 0)
        _pg_mouse.get_rel.return_value     = (0, 0)
        Input.update()
        # KEY_A estava ativo no frame anterior — deve agora gerar key_up
        assert Input.get_key_up(KEY_A) is True

    def test_update_detects_key_down(self):
        Input._keys_current = no_keys()
        _pg_key.get_pressed.return_value   = keys(KEY_D)
        _pg_mouse.get_pressed.return_value = (False, False, False)
        _pg_mouse.get_pos.return_value     = (0, 0)
        _pg_mouse.get_rel.return_value     = (0, 0)
        Input.update()
        assert Input.get_key_down(KEY_D) is True

    def test_update_advances_mouse_state(self):
        Input._mouse_current = (False, False, False)
        _pg_key.get_pressed.return_value   = no_keys()
        _pg_mouse.get_pressed.return_value = (True, False, False)
        _pg_mouse.get_pos.return_value     = (0, 0)
        _pg_mouse.get_rel.return_value     = (0, 0)
        Input.update()
        assert Input.get_mouse_button_down(0) is True
