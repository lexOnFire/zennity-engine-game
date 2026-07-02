"""
tests/core/test_input.py
────────────────────────────────────────────────────────────────
Commit 9: valida o contrato público de Input.
Todos os testes injetam estados diretamente nos atributos de classe,
evitando dependência de pygame.key.get_pressed() / pygame.mouse.*
"""
from __future__ import annotations

import pytest
import pygame


# ---------------------------------------------------------------------------
# Helper: cria um wrapper de teclas fake
# ---------------------------------------------------------------------------

def _make_keys(*pressed_keys):
    """Retorna uma lista de 512 bools com as teclas indicadas ativas."""
    keys = [False] * 512
    for k in pressed_keys:
        if 0 <= k < 512:
            keys[k] = True
    return keys


# ===========================================================================
# 1. get_key
# ===========================================================================

class TestGetKey:
    def test_held_key_returns_true(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_a)
        assert Input.get_key(pygame.K_a) is True

    def test_not_held_returns_false(self):
        from engine.input import Input
        Input._keys_current = _make_keys()
        assert Input.get_key(pygame.K_a) is False

    def test_empty_state_returns_false(self):
        from engine.input import Input
        Input._keys_current = []
        assert Input.get_key(pygame.K_SPACE) is False

    def test_invalid_key_returns_false(self):
        from engine.input import Input
        Input._keys_current = _make_keys()
        assert Input.get_key(9999) is False


# ===========================================================================
# 2. get_key_down
# ===========================================================================

class TestGetKeyDown:
    def test_key_down_only_on_first_frame(self):
        from engine.input import Input
        Input._keys_previous = _make_keys()          # não estava pressionado
        Input._keys_current  = _make_keys(pygame.K_a)  # agora está
        assert Input.get_key_down(pygame.K_a) is True

    def test_key_down_false_when_held(self):
        """Quando já estava pressionado no frame anterior, não é 'down'."""
        from engine.input import Input
        Input._keys_previous = _make_keys(pygame.K_a)
        Input._keys_current  = _make_keys(pygame.K_a)
        assert Input.get_key_down(pygame.K_a) is False

    def test_key_down_false_when_not_pressed(self):
        from engine.input import Input
        Input._keys_previous = _make_keys()
        Input._keys_current  = _make_keys()
        assert Input.get_key_down(pygame.K_a) is False

    def test_key_down_empty_state_safe(self):
        from engine.input import Input
        Input._keys_previous = []
        Input._keys_current  = []
        assert Input.get_key_down(pygame.K_a) is False


# ===========================================================================
# 3. get_key_up
# ===========================================================================

class TestGetKeyUp:
    def test_key_up_on_release_frame(self):
        from engine.input import Input
        Input._keys_previous = _make_keys(pygame.K_SPACE)
        Input._keys_current  = _make_keys()             # soltou
        assert Input.get_key_up(pygame.K_SPACE) is True

    def test_key_up_false_while_held(self):
        from engine.input import Input
        Input._keys_previous = _make_keys(pygame.K_SPACE)
        Input._keys_current  = _make_keys(pygame.K_SPACE)
        assert Input.get_key_up(pygame.K_SPACE) is False

    def test_key_up_false_when_never_pressed(self):
        from engine.input import Input
        Input._keys_previous = _make_keys()
        Input._keys_current  = _make_keys()
        assert Input.get_key_up(pygame.K_SPACE) is False


# ===========================================================================
# 4. Mouse position e rel
# ===========================================================================

class TestMousePosition:
    def test_get_mouse_position(self):
        from engine.input import Input
        Input._mouse_position = (320, 240)
        assert Input.get_mouse_position() == (320, 240)

    def test_get_mouse_rel(self):
        from engine.input import Input
        Input._mouse_rel = (5, -3)
        assert Input.get_mouse_rel() == (5, -3)


# ===========================================================================
# 5. Mouse buttons
# ===========================================================================

class TestMouseButton:
    def test_button_held_returns_true(self):
        from engine.input import Input
        Input._mouse_current = (True, False, False)
        assert Input.get_mouse_button(0) is True

    def test_button_not_held_returns_false(self):
        from engine.input import Input
        Input._mouse_current = (False, False, False)
        assert Input.get_mouse_button(0) is False

    def test_button_invalid_index_safe(self):
        from engine.input import Input
        Input._mouse_current = (False, False, False)
        assert Input.get_mouse_button(99) is False

    def test_button_down_first_frame(self):
        from engine.input import Input
        Input._mouse_previous = (False, False, False)
        Input._mouse_current  = (True,  False, False)
        assert Input.get_mouse_button_down(0) is True

    def test_button_down_false_when_held(self):
        from engine.input import Input
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_down(0) is False

    def test_button_up_on_release(self):
        from engine.input import Input
        Input._mouse_previous = (True,  False, False)
        Input._mouse_current  = (False, False, False)
        assert Input.get_mouse_button_up(0) is True

    def test_button_up_false_while_held(self):
        from engine.input import Input
        Input._mouse_previous = (True, False, False)
        Input._mouse_current  = (True, False, False)
        assert Input.get_mouse_button_up(0) is False

    def test_right_button(self):
        from engine.input import Input
        Input._mouse_current = (False, False, True)
        assert Input.get_mouse_button(2) is True


# ===========================================================================
# 6. Axes
# ===========================================================================

class TestAxes:
    def test_horizontal_left_arrow(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_LEFT)
        assert Input.get_axis_horizontal() == pytest.approx(-1.0)

    def test_horizontal_right_arrow(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_RIGHT)
        assert Input.get_axis_horizontal() == pytest.approx(1.0)

    def test_horizontal_a_key(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_a)
        assert Input.get_axis_horizontal() == pytest.approx(-1.0)

    def test_horizontal_d_key(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_d)
        assert Input.get_axis_horizontal() == pytest.approx(1.0)

    def test_horizontal_neutral(self):
        from engine.input import Input
        Input._keys_current = _make_keys()
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    def test_horizontal_both_cancel(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_LEFT, pygame.K_RIGHT)
        assert Input.get_axis_horizontal() == pytest.approx(0.0)

    def test_vertical_up_arrow(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_UP)
        assert Input.get_axis_vertical() == pytest.approx(-1.0)

    def test_vertical_down_arrow(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_DOWN)
        assert Input.get_axis_vertical() == pytest.approx(1.0)

    def test_vertical_w_key(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_w)
        assert Input.get_axis_vertical() == pytest.approx(-1.0)

    def test_vertical_s_key(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_s)
        assert Input.get_axis_vertical() == pytest.approx(1.0)

    def test_vertical_neutral(self):
        from engine.input import Input
        Input._keys_current = _make_keys()
        assert Input.get_axis_vertical() == pytest.approx(0.0)

    def test_vertical_both_cancel(self):
        from engine.input import Input
        Input._keys_current = _make_keys(pygame.K_UP, pygame.K_DOWN)
        assert Input.get_axis_vertical() == pytest.approx(0.0)


# ===========================================================================
# 7. update() rotaciona os estados
# ===========================================================================

class TestUpdate:
    def test_update_rotates_key_state(self):
        """Após update(), _keys_previous deve ser o que era _keys_current."""
        from engine.input import Input
        from unittest.mock import patch

        new_keys = _make_keys(pygame.K_SPACE)
        with patch("engine.input.pygame.key.get_pressed", return_value=new_keys), \
             patch("engine.input.pygame.mouse.get_pressed", return_value=(False,False,False)), \
             patch("engine.input.pygame.mouse.get_pos", return_value=(0,0)), \
             patch("engine.input.pygame.mouse.get_rel", return_value=(0,0)):
            old_current = Input._keys_current
            Input.update()
            assert Input._keys_previous is old_current

    def test_update_sets_new_current(self):
        from engine.input import Input
        from unittest.mock import patch

        new_keys = _make_keys(pygame.K_RETURN)
        with patch("engine.input.pygame.key.get_pressed", return_value=new_keys), \
             patch("engine.input.pygame.mouse.get_pressed", return_value=(False,False,False)), \
             patch("engine.input.pygame.mouse.get_pos", return_value=(100,200)), \
             patch("engine.input.pygame.mouse.get_rel", return_value=(1,2)):
            Input.update()
            assert Input._keys_current is new_keys
            assert Input._mouse_position == (100, 200)
