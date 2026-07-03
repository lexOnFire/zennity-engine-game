"""
tests/test_audio.py
=================================================================
Testes para engine/audio.py (AudioManager) — mixer headless.

Estrategia:
  - pygame.mixer inicializado com SDL_AUDIODRIVER=dummy
  - pygame.mixer.music patcheado com MagicMock para evitar
    carregamento real de arquivos
  - os.path.exists patcheado para simular arquivos presentes/ausentes
  - Sound patcheado para evitar I/O
  - Cada teste reseta o estado de classe do AudioManager via fixture
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# --------------------------------------------------------------------------
# Fixture: reseta estado de classe antes de cada teste
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_audio_manager():
    from engine.audio import AudioManager
    AudioManager._initialized = False
    AudioManager._sound_cache = {}
    AudioManager._master_volume = 1.0
    AudioManager._sfx_volume = 1.0
    AudioManager._music_volume = 1.0
    AudioManager._music_path = None
    AudioManager._music_paused = False
    yield
    # limpeza pos-teste
    AudioManager._sound_cache.clear()
    AudioManager._music_path = None
    AudioManager._music_paused = False


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def make_mock_sound():
    s = MagicMock(spec=pygame.mixer.Sound)
    s.play.return_value = MagicMock()  # Channel mock
    return s


# ==========================================================================
# _init
# ==========================================================================

class TestInit:
    def test_init_sets_initialized_true(self):
        from engine.audio import AudioManager
        result = AudioManager._init()
        assert result is True
        assert AudioManager._initialized is True

    def test_init_idempotent(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._init()
        assert AudioManager._initialized is True

    def test_init_returns_true_when_already_initialized(self):
        from engine.audio import AudioManager
        AudioManager._initialized = True
        assert AudioManager._init() is True


# ==========================================================================
# Volumes — clamp e propagacao
# ==========================================================================

class TestVolumes:
    def test_set_master_volume_clamps_to_zero(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager.set_master_volume(-5.0)
        assert AudioManager._master_volume == pytest.approx(0.0)

    def test_set_master_volume_clamps_to_one(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager.set_master_volume(99.0)
        assert AudioManager._master_volume == pytest.approx(1.0)

    def test_set_master_volume_mid_value(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager.set_master_volume(0.4)
        assert AudioManager._master_volume == pytest.approx(0.4)

    def test_set_sfx_volume_clamps(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager.set_sfx_volume(2.0)
        assert AudioManager._sfx_volume == pytest.approx(1.0)
        AudioManager.set_sfx_volume(-1.0)
        assert AudioManager._sfx_volume == pytest.approx(0.0)

    def test_set_music_volume_clamps(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager.set_music_volume(1.5)
        assert AudioManager._music_volume == pytest.approx(1.0)
        AudioManager.set_music_volume(-0.1)
        assert AudioManager._music_volume == pytest.approx(0.0)

    def test_set_master_volume_propagates_to_cached_sounds(self):
        from engine.audio import AudioManager
        AudioManager._init()
        mock = make_mock_sound()
        AudioManager._sound_cache["sfx.wav"] = mock
        AudioManager.set_master_volume(0.5)
        mock.set_volume.assert_called_with(
            pytest.approx(AudioManager._sfx_volume * 0.5)
        )

    def test_set_sfx_volume_propagates_to_cached_sounds(self):
        from engine.audio import AudioManager
        AudioManager._init()
        mock = make_mock_sound()
        AudioManager._sound_cache["sfx.wav"] = mock
        AudioManager.set_sfx_volume(0.3)
        mock.set_volume.assert_called_with(
            pytest.approx(0.3 * AudioManager._master_volume)
        )


# ==========================================================================
# play_music
# ==========================================================================

class TestPlayMusic:
    def test_play_music_file_not_found_no_crash(self):
        from engine.audio import AudioManager
        AudioManager.play_music("nao_existe.ogg")
        assert AudioManager._music_path is None

    def test_play_music_loads_and_plays(self):
        from engine.audio import AudioManager
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.music") as mock_music:
            mock_music.get_busy.return_value = True
            AudioManager.play_music("theme.ogg", loop=True, fade_ms=0)
            mock_music.load.assert_called_once_with("theme.ogg")
            mock_music.play.assert_called_once_with(-1, fade_ms=0)
            assert AudioManager._music_path == "theme.ogg"

    def test_play_music_no_loop(self):
        from engine.audio import AudioManager
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.music") as mock_music:
            AudioManager.play_music("theme.ogg", loop=False)
            mock_music.play.assert_called_once_with(0, fade_ms=0)

    def test_play_music_sets_volume(self):
        from engine.audio import AudioManager
        AudioManager._master_volume = 0.8
        AudioManager._music_volume = 0.5
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.music") as mock_music:
            AudioManager.play_music("theme.ogg")
            mock_music.set_volume.assert_called_with(pytest.approx(0.4))

    def test_play_music_not_initialized_still_no_crash(self):
        from engine.audio import AudioManager
        with patch.object(AudioManager, "_init", return_value=False):
            AudioManager.play_music("theme.ogg")
            assert AudioManager._music_path is None


# ==========================================================================
# stop / pause / resume music
# ==========================================================================

class TestMusicControl:
    def test_stop_music_clears_path(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_path = "theme.ogg"
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.stop_music()
            mock_music.stop.assert_called_once()
        assert AudioManager._music_path is None

    def test_stop_music_with_fade(self):
        from engine.audio import AudioManager
        AudioManager._init()
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.stop_music(fade_ms=500)
            mock_music.fadeout.assert_called_once_with(500)
            mock_music.stop.assert_not_called()

    def test_pause_music_sets_flag(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = False
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.pause_music()
            mock_music.pause.assert_called_once()
        assert AudioManager._music_paused is True

    def test_pause_music_idempotent(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = True
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.pause_music()
            mock_music.pause.assert_not_called()

    def test_resume_music_clears_flag(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = True
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.resume_music()
            mock_music.unpause.assert_called_once()
        assert AudioManager._music_paused is False

    def test_resume_music_idempotent(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = False
        with patch("pygame.mixer.music") as mock_music:
            AudioManager.resume_music()
            mock_music.unpause.assert_not_called()

    def test_is_music_playing_true(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = False
        with patch("pygame.mixer.music") as mock_music:
            mock_music.get_busy.return_value = True
            assert AudioManager.is_music_playing() is True

    def test_is_music_playing_false_when_paused(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = True
        with patch("pygame.mixer.music") as mock_music:
            mock_music.get_busy.return_value = True
            assert AudioManager.is_music_playing() is False

    def test_is_music_playing_false_when_not_busy(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = False
        with patch("pygame.mixer.music") as mock_music:
            mock_music.get_busy.return_value = False
            assert AudioManager.is_music_playing() is False


# ==========================================================================
# _load_sfx / play_sfx
# ==========================================================================

class TestSFX:
    def test_load_sfx_returns_none_if_file_missing(self):
        from engine.audio import AudioManager
        AudioManager._init()
        result = AudioManager._load_sfx("nao_existe.wav")
        assert result is None

    def test_load_sfx_caches_sound(self):
        from engine.audio import AudioManager
        mock = make_mock_sound()
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.Sound", return_value=mock):
            s1 = AudioManager._load_sfx("jump.wav")
            s2 = AudioManager._load_sfx("jump.wav")
        assert s1 is s2
        assert "jump.wav" in AudioManager._sound_cache

    def test_load_sfx_does_not_reload_cached(self):
        from engine.audio import AudioManager
        mock = make_mock_sound()
        AudioManager._sound_cache["jump.wav"] = mock
        with patch("pygame.mixer.Sound") as MockSound:
            AudioManager._load_sfx("jump.wav")
            MockSound.assert_not_called()

    def test_play_sfx_file_not_found_returns_none(self):
        from engine.audio import AudioManager
        AudioManager._init()
        result = AudioManager.play_sfx("nao_existe.wav")
        assert result is None

    def test_play_sfx_calls_play(self):
        from engine.audio import AudioManager
        mock = make_mock_sound()
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.Sound", return_value=mock):
            AudioManager.play_sfx("jump.wav", volume=1.0)
        mock.play.assert_called_once_with(0)

    def test_play_sfx_applies_effective_volume(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._master_volume = 0.5
        AudioManager._sfx_volume = 0.5
        mock = make_mock_sound()
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.Sound", return_value=mock):
            AudioManager.play_sfx("jump.wav", volume=1.0)
        mock.set_volume.assert_called_with(pytest.approx(0.25))

    def test_play_sfx_volume_clamps_to_one(self):
        from engine.audio import AudioManager
        AudioManager._init()
        mock = make_mock_sound()
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.Sound", return_value=mock):
            AudioManager.play_sfx("jump.wav", volume=999.0)
        args = mock.set_volume.call_args[0]
        assert args[0] <= 1.0

    def test_play_sfx_loops_param_passed(self):
        from engine.audio import AudioManager
        mock = make_mock_sound()
        with patch("os.path.exists", return_value=True), \
             patch("pygame.mixer.Sound", return_value=mock):
            AudioManager.play_sfx("jump.wav", loops=-1)
        mock.play.assert_called_once_with(-1)

    def test_stop_sfx_calls_stop(self):
        from engine.audio import AudioManager
        mock = make_mock_sound()
        AudioManager._sound_cache["jump.wav"] = mock
        AudioManager.stop_sfx("jump.wav")
        mock.stop.assert_called_once()

    def test_stop_sfx_unknown_path_no_crash(self):
        from engine.audio import AudioManager
        AudioManager.stop_sfx("nao_existe.wav")  # sem crash


# ==========================================================================
# Controle global: pause_all / resume_all / stop_all / unload_cache
# ==========================================================================

class TestGlobalControl:
    def test_stop_all_clears_music_path(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_path = "theme.ogg"
        with patch("pygame.mixer.music") as mm, \
             patch("pygame.mixer.stop"):
            AudioManager.stop_all()
        assert AudioManager._music_path is None

    def test_unload_cache_stops_and_clears(self):
        from engine.audio import AudioManager
        AudioManager._init()
        m1, m2 = make_mock_sound(), make_mock_sound()
        AudioManager._sound_cache = {"a.wav": m1, "b.wav": m2}
        AudioManager.unload_cache()
        m1.stop.assert_called_once()
        m2.stop.assert_called_once()
        assert len(AudioManager._sound_cache) == 0

    def test_pause_all_pauses_music_and_channels(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = False
        with patch("pygame.mixer.music") as mm, \
             patch("pygame.mixer.pause") as mp:
            AudioManager.pause_all()
            mm.pause.assert_called_once()
            mp.assert_called_once()

    def test_resume_all_resumes_music_and_channels(self):
        from engine.audio import AudioManager
        AudioManager._init()
        AudioManager._music_paused = True
        with patch("pygame.mixer.music") as mm, \
             patch("pygame.mixer.unpause") as mu:
            AudioManager.resume_all()
            mm.unpause.assert_called_once()
            mu.assert_called_once()
