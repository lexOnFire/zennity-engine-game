"""
tests/graphics/test_camera2d.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/graphics/camera2d.py.

Estratégia de isolamento:
  - Camera2D herda de Component. Component é importado diretamente;
    game_object é um MagicMock com transform.position como np.ndarray
    mutável, simulando o comportamento real da engine.
  - Camera2D.main é resetado para None em cada teste via fixture
    autouse para evitar vazão de estado entre testes.
  - target é um MagicMock com transform.position.
  - Todos os valores numéricos verificados com pytest.approx (1e-6).
"""
from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import MagicMock

from engine.graphics.camera2d import Camera2D


# ── helpers ────────────────────────────────────────────────────────────────

def _make_go(x=0.0, y=0.0):
    """Cria um game_object mock com transform.position mutável."""
    go = MagicMock()
    go.transform.position = np.array([x, y], dtype=float)
    return go


def _make_cam(x=0.0, y=0.0, zoom=1.0, smoothness=0.1, bounds=None, offset=(0.0, 0.0), target=None):
    """Cria uma Camera2D com game_object já atribuído."""
    cam = Camera2D(zoom=zoom, smoothness=smoothness, bounds=bounds, offset=offset, target=target)
    cam.game_object = _make_go(x, y)
    cam.transform   = cam.game_object.transform
    return cam


# ── fixture autouse ──────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def reset_main():
    Camera2D.main = None
    yield
    Camera2D.main = None


# ────────────────────────────────────────────────────────────────────────────
class TestInit:
    def test_default_zoom(self):
        cam = Camera2D()
        assert cam.zoom == pytest.approx(1.0)

    def test_default_smoothness(self):
        cam = Camera2D()
        assert cam.smoothness == pytest.approx(0.1)

    def test_default_target_none(self):
        cam = Camera2D()
        assert cam.target is None

    def test_default_bounds_none(self):
        cam = Camera2D()
        assert cam.bounds is None

    def test_default_offset(self):
        cam = Camera2D()
        assert cam.offset == (0.0, 0.0)

    def test_first_camera_becomes_main(self):
        cam = Camera2D()
        assert Camera2D.main is cam

    def test_second_camera_does_not_replace_main(self):
        cam1 = Camera2D()
        cam2 = Camera2D()
        assert Camera2D.main is cam1

    def test_custom_zoom(self):
        cam = Camera2D(zoom=2.5)
        assert cam.zoom == pytest.approx(2.5)

    def test_custom_bounds(self):
        b = (0, 0, 100, 100)
        cam = Camera2D(bounds=b)
        assert cam.bounds == b


# ────────────────────────────────────────────────────────────────────────────
class TestMakeMain:
    def test_make_main_replaces_main(self):
        cam1 = _make_cam()
        cam2 = _make_cam()
        cam2.make_main()
        assert Camera2D.main is cam2

    def test_start_sets_main_when_none(self):
        cam = _make_cam()
        Camera2D.main = None
        cam.start()
        assert Camera2D.main is cam

    def test_start_does_not_replace_existing_main(self):
        cam1 = _make_cam()
        Camera2D.main = cam1
        cam2 = _make_cam()
        cam2.start()
        assert Camera2D.main is cam1


# ────────────────────────────────────────────────────────────────────────────
class TestUpdateFollow:
    def _target(self, x, y):
        t = MagicMock()
        t.transform.position = np.array([x, y], dtype=float)
        return t

    def test_no_target_position_unchanged(self):
        cam = _make_cam(x=5.0, y=5.0)
        cam.update(0.1)
        assert cam.transform.position[0] == pytest.approx(5.0)
        assert cam.transform.position[1] == pytest.approx(5.0)

    def test_no_game_object_no_crash(self):
        cam = Camera2D(target=self._target(10, 10))
        cam.game_object = None
        cam.update(0.1)  # não deve lançar

    def test_instant_follow_smoothness_zero(self):
        tgt = self._target(100.0, 200.0)
        cam = _make_cam(target=tgt, smoothness=0.0)
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(100.0)
        assert cam.transform.position[1] == pytest.approx(200.0)

    def test_smooth_follow_moves_toward_target(self):
        tgt = self._target(100.0, 0.0)
        cam = _make_cam(x=0.0, smoothness=0.1)
        cam.target = tgt
        cam.update(0.016)
        # deve ter se movido para mais perto de 100
        assert 0.0 < cam.transform.position[0] < 100.0

    def test_smooth_follow_does_not_overshoot(self):
        tgt = self._target(100.0, 0.0)
        cam = _make_cam(x=0.0, smoothness=0.1)
        cam.target = tgt
        for _ in range(1000):
            cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(100.0, abs=1e-3)

    def test_offset_applied_to_target(self):
        tgt = self._target(50.0, 50.0)
        cam = _make_cam(target=tgt, smoothness=0.0, offset=(10.0, -5.0))
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(60.0)
        assert cam.transform.position[1] == pytest.approx(45.0)

    def test_large_dt_clamps_lerp_to_1(self):
        """dt muito grande não deve causar overshoot."""
        tgt = self._target(200.0, 0.0)
        cam = _make_cam(x=0.0, smoothness=0.1)
        cam.target = tgt
        cam.update(999.0)
        assert cam.transform.position[0] == pytest.approx(200.0)


# ────────────────────────────────────────────────────────────────────────────
class TestBounds:
    def _target(self, x, y):
        t = MagicMock()
        t.transform.position = np.array([x, y], dtype=float)
        return t

    def test_clamp_x_min(self):
        tgt = self._target(-999.0, 0.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=(0.0, 0.0, 500.0, 500.0))
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(0.0)

    def test_clamp_x_max(self):
        tgt = self._target(9999.0, 0.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=(0.0, 0.0, 500.0, 500.0))
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(500.0)

    def test_clamp_y_min(self):
        tgt = self._target(0.0, -999.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=(0.0, 0.0, 500.0, 500.0))
        cam.update(0.016)
        assert cam.transform.position[1] == pytest.approx(0.0)

    def test_clamp_y_max(self):
        tgt = self._target(0.0, 9999.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=(0.0, 0.0, 500.0, 500.0))
        cam.update(0.016)
        assert cam.transform.position[1] == pytest.approx(500.0)

    def test_inside_bounds_unchanged(self):
        tgt = self._target(250.0, 250.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=(0.0, 0.0, 500.0, 500.0))
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(250.0)
        assert cam.transform.position[1] == pytest.approx(250.0)

    def test_no_bounds_no_clamp(self):
        tgt = self._target(9999.0, 9999.0)
        cam = _make_cam(target=tgt, smoothness=0.0, bounds=None)
        cam.update(0.016)
        assert cam.transform.position[0] == pytest.approx(9999.0)


# ────────────────────────────────────────────────────────────────────────────
class TestWorldToScreen:
    def test_origin_maps_to_screen_center(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        sx, sy = cam.world_to_screen(np.array([0.0, 0.0]), 800, 600)
        assert sx == pytest.approx(400.0)
        assert sy == pytest.approx(300.0)

    def test_positive_world_x_right_of_center(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        sx, _ = cam.world_to_screen(np.array([100.0, 0.0]), 800, 600)
        assert sx == pytest.approx(500.0)

    def test_negative_world_x_left_of_center(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        sx, _ = cam.world_to_screen(np.array([-100.0, 0.0]), 800, 600)
        assert sx == pytest.approx(300.0)

    def test_zoom_scales_offset(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=2.0)
        sx, _ = cam.world_to_screen(np.array([100.0, 0.0]), 800, 600)
        # (100 - 0) * 2 + 400 = 600
        assert sx == pytest.approx(600.0)

    def test_camera_offset_shifts_result(self):
        cam = _make_cam(x=50.0, y=0.0, zoom=1.0)
        sx, _ = cam.world_to_screen(np.array([50.0, 0.0]), 800, 600)
        # (50 - 50) * 1 + 400 = 400
        assert sx == pytest.approx(400.0)

    def test_different_screen_sizes(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        sx, sy = cam.world_to_screen(np.array([0.0, 0.0]), 1920, 1080)
        assert sx == pytest.approx(960.0)
        assert sy == pytest.approx(540.0)


# ────────────────────────────────────────────────────────────────────────────
class TestScreenToWorld:
    def test_screen_center_maps_to_origin(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        wx, wy = cam.screen_to_world((400.0, 300.0), 800, 600)
        assert wx == pytest.approx(0.0)
        assert wy == pytest.approx(0.0)

    def test_right_of_center_is_positive_world_x(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=1.0)
        wx, _ = cam.screen_to_world((500.0, 300.0), 800, 600)
        assert wx == pytest.approx(100.0)

    def test_zoom_2_halves_world_coords(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=2.0)
        wx, _ = cam.screen_to_world((600.0, 300.0), 800, 600)
        # (600 - 400) / 2 + 0 = 100
        assert wx == pytest.approx(100.0)

    def test_roundtrip_world_screen_world(self):
        cam = _make_cam(x=37.0, y=-22.0, zoom=1.5)
        world_in = np.array([120.0, -80.0])
        sx, sy = cam.world_to_screen(world_in, 1024, 768)
        wx, wy = cam.screen_to_world((sx, sy), 1024, 768)
        assert wx == pytest.approx(120.0, abs=1e-5)
        assert wy == pytest.approx(-80.0, abs=1e-5)

    def test_roundtrip_screen_world_screen(self):
        cam = _make_cam(x=0.0, y=0.0, zoom=3.0)
        screen_in = (300.0, 200.0)
        wx, wy = cam.screen_to_world(screen_in, 800, 600)
        sx, sy = cam.world_to_screen(np.array([wx, wy]), 800, 600)
        assert sx == pytest.approx(300.0, abs=1e-5)
        assert sy == pytest.approx(200.0, abs=1e-5)

    def test_camera_offset_shifts_world(self):
        cam = _make_cam(x=100.0, y=0.0, zoom=1.0)
        wx, _ = cam.screen_to_world((400.0, 300.0), 800, 600)
        assert wx == pytest.approx(100.0)
