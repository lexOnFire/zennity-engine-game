"""
tests/test_assets.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/assets.py.

Estratégia de isolamento:
  - pygame, pygame.mixer, pygame.font, pygame.image são todos stubados
    via sys.modules antes do import. Nenhuma janela, nenhum init real.
  - os.path.exists e os.path.isfile são patchados por teste para simular
    arquivos presentes ou ausentes sem tocar o disco.
  - Assets._images/_sounds/_fonts/_meshes são limpos em cada teste pelo
    fixture autouse, garantindo isolamento de cache.
  - Mesh é testado de forma pura: np.ndarray real, sem pygame.
"""
from __future__ import annotations

import sys
import os
import io
from types import ModuleType
from unittest.mock import MagicMock, patch, mock_open

import numpy as np
import pytest

# ── stub pygame ──────────────────────────────────────────────────────────────

class _FakeSurface:
    SRCALPHA = 0x00010000
    def __init__(self, size=(32, 32), flags=0):
        self._size = tuple(size)
        self.blit        = MagicMock()
        self.fill        = MagicMock()
        self.get_size    = MagicMock(return_value=self._size)
        self.convert_alpha = MagicMock(return_value=self)
        self.convert       = MagicMock(return_value=self)


if "pygame" not in sys.modules:
    _pg                     = ModuleType("pygame")
    _pg.Surface             = _FakeSurface
    _pg.SRCALPHA            = _FakeSurface.SRCALPHA

    # pygame.mixer
    _mixer                  = ModuleType("pygame.mixer")
    _mixer.Sound            = MagicMock(return_value=MagicMock())
    _mixer.music            = MagicMock()
    _mixer.music.load       = MagicMock()
    _mixer.music.set_volume = MagicMock()
    _mixer.music.play       = MagicMock()
    _pg.mixer               = _mixer

    # pygame.image
    _image                  = ModuleType("pygame.image")
    _image.load             = MagicMock(return_value=_FakeSurface())
    _pg.image               = _image

    # pygame.font
    _font_mod               = ModuleType("pygame.font")
    _font_mod.SysFont       = MagicMock(return_value=MagicMock())
    _font_mod.Font          = MagicMock(return_value=MagicMock())
    _pg.font                = _font_mod

    sys.modules["pygame"]         = _pg
    sys.modules["pygame.mixer"]   = _mixer
    sys.modules["pygame.image"]   = _image
    sys.modules["pygame.font"]    = _font_mod
else:
    _pg      = sys.modules["pygame"]
    _mixer   = sys.modules.get("pygame.mixer", _pg.mixer)
    _image   = sys.modules.get("pygame.image", _pg.image)
    _font_mod = sys.modules.get("pygame.font", _pg.font)

from engine.assets import Assets, Mesh  # noqa: E402


@pytest.fixture(autouse=True)
def clean_cache():
    """Limpa todos os caches de classe entre testes."""
    Assets._images.clear()
    Assets._sounds.clear()
    Assets._fonts.clear()
    Assets._meshes.clear()
    # Reset mocks
    _image.load.reset_mock()
    _mixer.Sound.reset_mock()
    _font_mod.SysFont.reset_mock()
    _font_mod.Font.reset_mock()
    _mixer.music.load.reset_mock()
    _mixer.music.set_volume.reset_mock()
    _mixer.music.play.reset_mock()
    yield
    Assets._images.clear()
    Assets._sounds.clear()
    Assets._fonts.clear()
    Assets._meshes.clear()


# ─────────────────────────────────────────────────────────────────────────────
class TestMeshInit:
    def test_vertices_stored_as_float32(self):
        m = Mesh(np.array([[0,0,0],[1,0,0],[0,1,0]]), [[0,1,2]])
        assert m.vertices.dtype == np.float32

    def test_faces_stored_as_list(self):
        faces = [[0, 1, 2]]
        m = Mesh(np.array([[0,0,0],[1,0,0],[0,1,0]]), faces)
        assert m.faces == faces

    def test_normals_none_when_not_provided(self):
        m = Mesh(np.array([[0,0,0],[1,0,0],[0,1,0]]), [[0,1,2]])
        assert m.vertex_normals is None

    def test_normals_stored_when_provided(self):
        n = np.array([[0,0,1]])
        m = Mesh(np.array([[0,0,0],[1,0,0],[0,1,0]]), [[0,1,2]], normals=n)
        assert m.vertex_normals is not None
        assert m.vertex_normals.dtype == np.float32

    def test_face_normals_calculated(self):
        verts = np.array([[0,0,0],[1,0,0],[0,1,0]], dtype=np.float32)
        m = Mesh(verts, [[0,1,2]])
        assert len(m.face_normals) == 1

    def test_face_normal_unit_length(self):
        verts = np.array([[0,0,0],[1,0,0],[0,1,0]], dtype=np.float32)
        m = Mesh(verts, [[0,1,2]])
        norm = np.linalg.norm(m.face_normals[0])
        assert norm == pytest.approx(1.0, abs=1e-5)

    def test_degenerate_face_fallback_normal(self):
        """Face com menos de 3 vértices recebe normal (0,0,1)."""
        verts = np.array([[0,0,0],[1,0,0],[0,1,0]], dtype=np.float32)
        m = Mesh(verts, [[0, 1]])   # face com 2 vértices
        assert list(m.face_normals[0]) == pytest.approx([0, 0, 1])

    def test_zero_cross_product_fallback(self):
        """Face colinear (produto vetorial zero) → fallback (0,0,1)."""
        verts = np.array([[0,0,0],[1,0,0],[2,0,0]], dtype=np.float32)
        m = Mesh(verts, [[0,1,2]])
        assert list(m.face_normals[0]) == pytest.approx([0, 0, 1])


# ─────────────────────────────────────────────────────────────────────────────
class TestGetImage:
    def test_image_loaded_when_file_exists(self):
        with patch("os.path.exists", return_value=True):
            _image.load.return_value = _FakeSurface()
            img = Assets.get_image("a.png")
        assert img is not None
        _image.load.assert_called_once_with("a.png")

    def test_image_cached_second_call_no_reload(self):
        with patch("os.path.exists", return_value=True):
            _image.load.return_value = _FakeSurface()
            Assets.get_image("a.png")
            Assets.get_image("a.png")
        _image.load.assert_called_once()

    def test_fallback_surface_when_missing(self):
        with patch("os.path.exists", return_value=False):
            img = Assets.get_image("missing.png")
        assert img is not None
        _image.load.assert_not_called()

    def test_fallback_cached(self):
        with patch("os.path.exists", return_value=False):
            a = Assets.get_image("x.png")
            b = Assets.get_image("x.png")
        assert a is b

    def test_alpha_true_calls_convert_alpha(self):
        fake = _FakeSurface()
        with patch("os.path.exists", return_value=True):
            _image.load.return_value = fake
            Assets.get_image("a.png", alpha=True)
        fake.convert_alpha.assert_called_once()

    def test_alpha_false_calls_convert(self):
        fake = _FakeSurface()
        with patch("os.path.exists", return_value=True):
            _image.load.return_value = fake
            Assets.get_image("a.png", alpha=False)
        fake.convert.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
class TestLoadSpriteSheet:
    def _make_sheet(self, w, h):
        fake = _FakeSurface((w, h))
        fake.get_size.return_value = (w, h)
        return fake

    def test_returns_list_of_frames(self):
        sheet = self._make_sheet(64, 32)
        with patch.object(Assets, "get_image", return_value=sheet):
            frames = Assets.load_sprite_sheet("sheet.png", 32, 32)
        assert isinstance(frames, list)

    def test_correct_frame_count_2x1(self):
        sheet = self._make_sheet(64, 32)
        with patch.object(Assets, "get_image", return_value=sheet):
            frames = Assets.load_sprite_sheet("sheet.png", 32, 32)
        assert len(frames) == 2

    def test_correct_frame_count_2x2(self):
        sheet = self._make_sheet(64, 64)
        with patch.object(Assets, "get_image", return_value=sheet):
            frames = Assets.load_sprite_sheet("sheet.png", 32, 32)
        assert len(frames) == 4

    def test_out_of_bounds_frames_skipped(self):
        """Sheet 70x32 com frame 32x32 → apenas 2 frames (70 não é múltiplo de 32)."""
        sheet = self._make_sheet(70, 32)
        with patch.object(Assets, "get_image", return_value=sheet):
            frames = Assets.load_sprite_sheet("sheet.png", 32, 32)
        assert len(frames) == 2

    def test_each_frame_is_surface(self):
        sheet = self._make_sheet(64, 32)
        with patch.object(Assets, "get_image", return_value=sheet):
            frames = Assets.load_sprite_sheet("sheet.png", 32, 32)
        # _FakeSurface é instanciado dentro do método; verifica que cada frame tem blit
        for f in frames:
            assert hasattr(f, "blit")


# ─────────────────────────────────────────────────────────────────────────────
class TestGetSound:
    def test_sound_loaded_when_file_exists(self):
        with patch("os.path.exists", return_value=True):
            snd = Assets.get_sound("boom.wav")
        assert snd is not None
        _mixer.Sound.assert_called_once_with("boom.wav")

    def test_sound_cached(self):
        with patch("os.path.exists", return_value=True):
            a = Assets.get_sound("boom.wav")
            b = Assets.get_sound("boom.wav")
        assert a is b
        _mixer.Sound.assert_called_once()

    def test_null_sound_when_missing(self):
        with patch("os.path.exists", return_value=False):
            snd = Assets.get_sound("missing.wav")
        _mixer.Sound.assert_not_called()
        # NullSound é calleable
        snd.play()
        snd.stop()
        snd.set_volume(0.5)

    def test_null_sound_cached(self):
        with patch("os.path.exists", return_value=False):
            a = Assets.get_sound("x.wav")
            b = Assets.get_sound("x.wav")
        assert a is b


# ─────────────────────────────────────────────────────────────────────────────
class TestPlayMusic:
    def test_play_music_calls_mixer(self):
        with patch("os.path.exists", return_value=True):
            Assets.play_music("bg.mp3")
        _mixer.music.load.assert_called_once_with("bg.mp3")
        _mixer.music.play.assert_called_once()

    def test_play_music_sets_volume(self):
        with patch("os.path.exists", return_value=True):
            Assets.play_music("bg.mp3", volume=0.8)
        _mixer.music.set_volume.assert_called_once_with(0.8)

    def test_play_music_loops(self):
        with patch("os.path.exists", return_value=True):
            Assets.play_music("bg.mp3", loops=0)
        args = _mixer.music.play.call_args[0]
        assert args[0] == 0

    def test_play_music_no_file_no_call(self):
        with patch("os.path.exists", return_value=False):
            Assets.play_music("missing.mp3")
        _mixer.music.load.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestGetFont:
    def test_sysfont_when_name_none(self):
        with patch("os.path.exists", return_value=False):
            Assets.get_font(None, 16)
        _font_mod.SysFont.assert_called_once()

    def test_sysfont_when_file_missing(self):
        with patch("os.path.exists", return_value=False):
            Assets.get_font("nonexistent.ttf", 24)
        _font_mod.SysFont.assert_called_once()

    def test_font_loaded_when_file_exists(self):
        with patch("os.path.exists", return_value=True):
            Assets.get_font("custom.ttf", 20)
        _font_mod.Font.assert_called_once_with("custom.ttf", 20)

    def test_font_cached_by_name_and_size(self):
        with patch("os.path.exists", return_value=True):
            a = Assets.get_font("f.ttf", 12)
            b = Assets.get_font("f.ttf", 12)
        assert a is b
        _font_mod.Font.assert_called_once()

    def test_different_sizes_create_different_entries(self):
        with patch("os.path.exists", return_value=True):
            Assets.get_font("f.ttf", 12)
            Assets.get_font("f.ttf", 24)
        assert _font_mod.Font.call_count == 2

    def test_none_name_cached_separately_per_size(self):
        with patch("os.path.exists", return_value=False):
            Assets.get_font(None, 10)
            Assets.get_font(None, 10)
        _font_mod.SysFont.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
class TestGetMesh:
    def test_fallback_cube_when_missing(self):
        with patch("os.path.exists", return_value=False):
            mesh = Assets.get_mesh("missing.obj")
        assert isinstance(mesh, Mesh)
        assert len(mesh.faces) == 6   # cubo tem 6 faces

    def test_mesh_cached(self):
        with patch("os.path.exists", return_value=False):
            a = Assets.get_mesh("x.obj")
            b = Assets.get_mesh("x.obj")
        assert a is b

    def test_load_obj_parses_vertices(self):
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("tri.obj")
        assert len(mesh.vertices) == 3

    def test_load_obj_parses_faces(self):
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("tri.obj")
        assert len(mesh.faces) == 1
        assert mesh.faces[0] == [0, 1, 2]   # 1-based → 0-based

    def test_load_obj_skips_comments(self):
        obj_content = "# comment\nv 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("c.obj")
        assert len(mesh.vertices) == 3

    def test_load_obj_parses_normals(self):
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\nf 1//1 2//1 3//1\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("n.obj")
        assert mesh.vertex_normals is not None
        assert len(mesh.vertex_normals) == 1

    def test_load_obj_face_slash_slash_format(self):
        """Formato v//vn (sem UV) deve ser parseado sem erro."""
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\nf 1//1 2//1 3//1\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("slash.obj")
        assert len(mesh.faces) == 1

    def test_load_obj_face_slash_uv_format(self):
        """Formato v/uv/vn deve ser parseado sem erro."""
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 1\nf 1/1/1 2/2/1 3/3/1\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("uv.obj")
        assert len(mesh.faces) == 1

    def test_load_obj_negative_indices(self):
        """OBJ suporta índices negativos (relativos ao final)."""
        obj_content = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf -3 -2 -1\n"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=obj_content)):
            mesh = Assets.get_mesh("neg.obj")
        assert mesh.faces[0] == [0, 1, 2]


# ─────────────────────────────────────────────────────────────────────────────
class TestCreateCubeMesh:
    def test_cube_has_8_vertices(self):
        m = Assets.create_cube_mesh()
        assert len(m.vertices) == 8

    def test_cube_has_6_faces(self):
        m = Assets.create_cube_mesh()
        assert len(m.faces) == 6

    def test_cube_custom_size(self):
        m = Assets.create_cube_mesh(size=4.0)
        # Todos os vértices devem ter coordenadas em [-2, 2]
        assert np.all(np.abs(m.vertices) <= 2.0 + 1e-6)

    def test_cube_face_normals_shape(self):
        m = Assets.create_cube_mesh()
        assert m.face_normals.shape == (6, 3)

    def test_cube_default_size_bounds(self):
        m = Assets.create_cube_mesh(size=1.0)
        assert np.all(np.abs(m.vertices) <= 0.5 + 1e-6)
