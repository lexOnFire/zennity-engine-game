"""
tests/test_audio.py
────────────────────────────────────────────────────────────────
Testes unitários de engine/audio.py (AudioManager).

Estratégia:
  - pygame.mixer e pygame.mixer.music são completamente mockados via
    sys.modules antes de qualquer import da engine.
  - os.path.exists é patchado para controlar se arquivos "existem".
  - Fixture autouse reseta o estado de classe do AudioManager antes de
    cada teste (volumes, cache, flags de música).
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch

import pytest

# ── stub pygame.mixer ────────────────────────────────────────────────────────
if "pygame" not in sys.modules:
    _pygame = ModuleType("pygame")
    sys.modules["pygame"] = _pygame
else:
    _pygame = sys.modules["pygame"]

_mixer = ModuleType("pygame.mixer")
_mixer.get_init   = MagicMock(return_value=True)
_mixer.init       = MagicMock()
_mixer.pause      = MagicMock()
_mixer.unpause    = MagicMock()
_mixer.stop       = MagicMock()
_music            = MagicMock()
_mixer.music      = _music

# pygame.mixer.Sound precisa ser uma classe mock
class _FakeSound:
    def __init__(self, path):
        self.path   = path
        self._vol   = 1.0
        self.play   = MagicMock(return_value=MagicMock())
        self.stop   = MagicMock()
        self.set_volume = MagicMock(side_effect=lambda v: setattr(self, "_vol", v))

_mixer.Sound    = _FakeSound
_mixer.Channel  = MagicMock
sys.modules["pygame.mixer"] = _mixer
_pygame.mixer = _mixer

# Garante que AudioManager reimporte pygame.mixer mockado
if "engine.audio" in sys.modules:
    del sys.modules["engine.audio"]

from engine.audio import AudioManager  # noqa: E402


@pytest.fixture(autouse=True)
def reset_manager():
    """Reseta estado de classe do AudioManager e os mocks entre testes."""
    AudioManager._initialized  = True   # mixer já está "inicializado" pelo stub
    AudioManager._sound_cache  = {}
    AudioManager._master_volume = 1.0
    AudioManager._sfx_volume    = 1.0
    AudioManager._music_volume  = 1.0
    AudioManager._music_path    = None
    AudioManager._music_paused  = False
    _music.reset_mock()
    _mixer.pause.reset_mock()
    _mixer.unpause.reset_mock()
    _mixer.stop.reset_mock()
    _mixer.get_init.return_value = True
    _music.get_busy.return_value = False
    yield


# ─────────────────────────────────────────────────────────────────────────────
class TestInit:
    def test_init_returns_true_when_mixer_ready(self):
        AudioManager._initialized = False
        _mixer.get_init.return_value = True
        assert AudioManager._init() is True
        assert AudioManager._initialized is True

    def test_init_calls_mixer_init_when_not_ready(self):
        AudioManager._initialized = False
        _mixer.get_init.return_value = False
        _mixer.init.reset_mock()
        AudioManager._init()
        _mixer.init.assert_called_once()

    def test_init_skips_when_already_initialized(self):
        AudioManager._initialized = True
        _mixer.init.reset_mock()
        AudioManager._init()
        _mixer.init.assert_not_called()

    def test_init_returns_false_on_exception(self):
        AudioManager._initialized = False
        _mixer.get_init.side_effect = RuntimeError("boom")
        result = AudioManager._init()
        _mixer.get_init.side_effect = None
        assert result is False


# ─────────────────────────────────────────────────────────────────────────────
class TestPlayMusic:
    def test_play_music_loads_file(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg")
        _music.load.assert_called_once_with("theme.ogg")

    def test_play_music_loops_by_default(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg")
        _music.play.assert_called_once()
        args, kwargs = _music.play.call_args
        assert args[0] == -1

    def test_play_music_no_loop(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg", loop=False)
        args, _ = _music.play.call_args
        assert args[0] == 0

    def test_play_music_sets_path(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg")
        assert AudioManager._music_path == "theme.ogg"

    def test_play_music_clears_paused_flag(self):
        AudioManager._music_paused = True
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg")
        assert AudioManager._music_paused is False

    def test_play_music_skips_missing_file(self):
        with patch("os.path.exists", return_value=False):
            AudioManager.play_music("ghost.ogg")
        _music.load.assert_not_called()

    def test_play_music_respects_volume(self):
        AudioManager._master_volume = 0.5
        AudioManager._music_volume  = 0.8
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg")
        _music.set_volume.assert_called()
        vol = _music.set_volume.call_args[0][0]
        assert vol == pytest.approx(0.4)

    def test_play_music_fade_ms_passed(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_music("theme.ogg", fade_ms=500)
        _, kwargs = _music.play.call_args
        assert kwargs.get("fade_ms") == 500


# ─────────────────────────────────────────────────────────────────────────────
class TestStopMusic:
    def test_stop_music_calls_stop(self):
        AudioManager.stop_music()
        _music.stop.assert_called_once()

    def test_stop_music_clears_path(self):
        AudioManager._music_path = "theme.ogg"
        AudioManager.stop_music()
        assert AudioManager._music_path is None

    def test_stop_music_clears_paused_flag(self):
        AudioManager._music_paused = True
        AudioManager.stop_music()
        assert AudioManager._music_paused is False

    def test_stop_music_fadeout_when_fade_ms(self):
        AudioManager.stop_music(fade_ms=300)
        _music.fadeout.assert_called_once_with(300)
        _music.stop.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
class TestPauseResumeMusic:
    def test_pause_sets_flag(self):
        AudioManager._music_paused = False
        AudioManager.pause_music()
        assert AudioManager._music_paused is True

    def test_pause_calls_mixer_pause(self):
        AudioManager.pause_music()
        _music.pause.assert_called_once()

    def test_pause_idempotent(self):
        AudioManager._music_paused = True
        AudioManager.pause_music()
        _music.pause.assert_not_called()

    def test_resume_clears_flag(self):
        AudioManager._music_paused = True
        AudioManager.resume_music()
        assert AudioManager._music_paused is False

    def test_resume_calls_mixer_unpause(self):
        AudioManager._music_paused = True
        AudioManager.resume_music()
        _music.unpause.assert_called_once()

    def test_resume_idempotent_when_not_paused(self):
        AudioManager._music_paused = False
        AudioManager.resume_music()
        _music.unpause.assert_not_called()

    def test_is_music_playing_true(self):
        _music.get_busy.return_value = True
        AudioManager._music_paused   = False
        assert AudioManager.is_music_playing() is True

    def test_is_music_playing_false_when_paused(self):
        _music.get_busy.return_value = True
        AudioManager._music_paused   = True
        assert AudioManager.is_music_playing() is False

    def test_is_music_playing_false_when_not_busy(self):
        _music.get_busy.return_value = False
        assert AudioManager.is_music_playing() is False


# ─────────────────────────────────────────────────────────────────────────────
class TestSetMusicVolume:
    def test_set_music_volume_clamps_above_one(self):
        AudioManager.set_music_volume(2.0)
        assert AudioManager._music_volume == pytest.approx(1.0)

    def test_set_music_volume_clamps_below_zero(self):
        AudioManager.set_music_volume(-0.5)
        assert AudioManager._music_volume == pytest.approx(0.0)

    def test_set_music_volume_applies_master(self):
        AudioManager._master_volume = 0.5
        AudioManager.set_music_volume(0.8)
        vol = _music.set_volume.call_args[0][0]
        assert vol == pytest.approx(0.4)


# ─────────────────────────────────────────────────────────────────────────────
class TestPlaySfx:
    def test_play_sfx_returns_channel(self):
        with patch("os.path.exists", return_value=True):
            ch = AudioManager.play_sfx("jump.wav")
        assert ch is not None

    def test_play_sfx_caches_sound(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav")
            AudioManager.play_sfx("jump.wav")
        assert len(AudioManager._sound_cache) == 1

    def test_play_sfx_missing_file_returns_none(self):
        with patch("os.path.exists", return_value=False):
            ch = AudioManager.play_sfx("ghost.wav")
        assert ch is None

    def test_play_sfx_volume_clamped_above_one(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav", volume=5.0)
        sound = AudioManager._sound_cache["jump.wav"]
        assert sound._vol == pytest.approx(1.0)

    def test_play_sfx_volume_clamped_below_zero(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav", volume=-1.0)
        sound = AudioManager._sound_cache["jump.wav"]
        assert sound._vol == pytest.approx(0.0)

    def test_play_sfx_applies_master_and_sfx_volume(self):
        AudioManager._master_volume = 0.5
        AudioManager._sfx_volume    = 0.4
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav", volume=1.0)
        sound = AudioManager._sound_cache["jump.wav"]
        assert sound._vol == pytest.approx(0.2)

    def test_play_sfx_calls_sound_play(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav", loops=2)
        sound = AudioManager._sound_cache["jump.wav"]
        sound.play.assert_called_once_with(2)

    def test_play_sfx_returns_none_when_not_initialized(self):
        AudioManager._initialized = False
        _mixer.get_init.return_value = False
        _mixer.init.side_effect = RuntimeError("no audio")
        with patch("os.path.exists", return_value=True):
            result = AudioManager.play_sfx("jump.wav")
        _mixer.init.side_effect = None
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
class TestStopSfx:
    def test_stop_sfx_calls_sound_stop(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("jump.wav")
        AudioManager.stop_sfx("jump.wav")
        sound = AudioManager._sound_cache["jump.wav"]
        sound.stop.assert_called_once()

    def test_stop_sfx_unknown_path_no_error(self):
        AudioManager.stop_sfx("ghost.wav")


# ─────────────────────────────────────────────────────────────────────────────
class TestSetSfxVolume:
    def test_set_sfx_volume_stores_value(self):
        AudioManager.set_sfx_volume(0.3)
        assert AudioManager._sfx_volume == pytest.approx(0.3)

    def test_set_sfx_volume_clamps_above_one(self):
        AudioManager.set_sfx_volume(3.0)
        assert AudioManager._sfx_volume == pytest.approx(1.0)

    def test_set_sfx_volume_clamps_below_zero(self):
        AudioManager.set_sfx_volume(-1.0)
        assert AudioManager._sfx_volume == pytest.approx(0.0)

    def test_set_sfx_volume_reapplies_to_cache(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("a.wav")
            AudioManager.play_sfx("b.wav")
        AudioManager.set_sfx_volume(0.5)
        for sound in AudioManager._sound_cache.values():
            assert sound._vol == pytest.approx(0.5)


# ─────────────────────────────────────────────────────────────────────────────
class TestMasterVolume:
    def test_set_master_volume_stores_value(self):
        AudioManager.set_master_volume(0.7)
        assert AudioManager._master_volume == pytest.approx(0.7)

    def test_set_master_volume_clamps_above_one(self):
        AudioManager.set_master_volume(99.0)
        assert AudioManager._master_volume == pytest.approx(1.0)

    def test_set_master_volume_clamps_below_zero(self):
        AudioManager.set_master_volume(-5.0)
        assert AudioManager._master_volume == pytest.approx(0.0)

    def test_set_master_volume_updates_music(self):
        AudioManager._music_volume = 0.5
        AudioManager.set_master_volume(0.4)
        vol = _music.set_volume.call_args[0][0]
        assert vol == pytest.approx(0.2)

    def test_set_master_volume_updates_sfx_cache(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("a.wav")
        AudioManager._sfx_volume = 0.5
        AudioManager.set_master_volume(0.4)
        sound = list(AudioManager._sound_cache.values())[0]
        assert sound._vol == pytest.approx(0.2)


# ─────────────────────────────────────────────────────────────────────────────
class TestGlobalControl:
    def test_pause_all_calls_mixer_pause(self):
        AudioManager.pause_all()
        _mixer.pause.assert_called_once()

    def test_pause_all_pauses_music(self):
        AudioManager.pause_all()
        assert AudioManager._music_paused is True

    def test_resume_all_calls_mixer_unpause(self):
        AudioManager._music_paused = True
        AudioManager.resume_all()
        _mixer.unpause.assert_called_once()

    def test_resume_all_resumes_music(self):
        AudioManager._music_paused = True
        AudioManager.resume_all()
        assert AudioManager._music_paused is False

    def test_stop_all_stops_mixer(self):
        AudioManager.stop_all()
        _mixer.stop.assert_called_once()

    def test_stop_all_clears_music_path(self):
        AudioManager._music_path = "theme.ogg"
        AudioManager.stop_all()
        assert AudioManager._music_path is None


# ─────────────────────────────────────────────────────────────────────────────
class TestUnloadCache:
    def test_unload_cache_clears_dict(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("a.wav")
            AudioManager.play_sfx("b.wav")
        AudioManager.unload_cache()
        assert len(AudioManager._sound_cache) == 0

    def test_unload_cache_stops_all_sounds(self):
        with patch("os.path.exists", return_value=True):
            AudioManager.play_sfx("a.wav")
        sounds = list(AudioManager._sound_cache.values())
        AudioManager.unload_cache()
        for s in sounds:
            s.stop.assert_called()

    def test_unload_cache_empty_is_noop(self):
        AudioManager.unload_cache()  # sem crash
