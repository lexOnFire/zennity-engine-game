"""
tests/test_audio.py
────────────────────────────────────────────────────────────────────────────
Testes unitários de engine/audio.py (AudioManager).

Estratégia de isolamento:
  - pygame.mixer completo é stubado (Sound, music, canais globais).
  - os.path.exists é patchado via monkeypatch para controlar se
    um arquivo "existe" sem tocar o sistema de arquivos real.
  - AudioManager é uma classe pura com estado de classe; a fixture
    `reset_audio` restaura todos os atributos entre testes.
  - Nenhum arquivo de áudio real é necessário.
"""
import sys
import pygame
import pytest
from types import ModuleType
from unittest.mock import MagicMock

# Salva o mixer real original antes de stubar
orig_mixer = getattr(pygame, "mixer", None)
orig_pygame_mixer_module = sys.modules.get("pygame.mixer")

@pytest.fixture(scope="module", autouse=True)
def cleanup_pygame_mixer():
    yield
    # Restaura o pygame.mixer real original
    import pygame
    if orig_mixer is not None:
        pygame.mixer = orig_mixer
    if orig_pygame_mixer_module is not None:
        sys.modules["pygame.mixer"] = orig_pygame_mixer_module
    elif "pygame.mixer" in sys.modules:
        del sys.modules["pygame.mixer"]
    
    # Restaura os estados estáticos do AudioManager
    from engine.audio import AudioManager
    AudioManager._initialized = False
    AudioManager._sound_cache = {}
    AudioManager._sources = []
    AudioManager._listeners = []


# ── stub pygame.mixer ─────────────────────────────────────────────────────────────

class _FakeMusic:
    def __init__(self):
        self.load        = MagicMock()
        self.play        = MagicMock()
        self.stop        = MagicMock()
        self.pause       = MagicMock()
        self.unpause     = MagicMock()
        self.fadeout     = MagicMock()
        self.set_volume  = MagicMock()
        self.get_busy    = MagicMock(return_value=False)


class _FakeSound:
    def __init__(self, path=""):
        self.path       = path
        self.set_volume = MagicMock()
        self.play       = MagicMock(return_value=MagicMock())  # returns Channel
        self.stop       = MagicMock()


def _build_mixer_stub():
    mixer = ModuleType("pygame.mixer")
    mixer.get_init  = MagicMock(return_value=True)
    mixer.init      = MagicMock()
    mixer.pause     = MagicMock()
    mixer.unpause   = MagicMock()
    mixer.stop      = MagicMock()
    mixer.music     = _FakeMusic()
    # Sound é uma factory que retorna _FakeSound
    mixer.Sound     = MagicMock(side_effect=lambda path: _FakeSound(path))
    return mixer


if "pygame" not in sys.modules:
    _pg = ModuleType("pygame")
    _pg_mixer = _build_mixer_stub()
    _pg.mixer = _pg_mixer
    sys.modules["pygame"]       = _pg
    sys.modules["pygame.mixer"] = _pg_mixer
else:
    _pg = sys.modules["pygame"]
    _pg_mixer = _build_mixer_stub()
    _pg.mixer = _pg_mixer
    sys.modules["pygame.mixer"] = _pg_mixer

from engine.audio import AudioManager  # noqa: E402


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_audio():
    """Reseta estado de classe e mocks do mixer antes de cada teste."""
    AudioManager._initialized   = True   # pula init() real
    AudioManager._sound_cache   = {}
    AudioManager._master_volume = 1.0
    AudioManager._sfx_volume    = 1.0
    AudioManager._music_volume  = 1.0
    AudioManager._music_path    = None
    AudioManager._music_paused  = False

    # refresca mocks do mixer
    _pg_mixer.music   = _FakeMusic()
    _pg_mixer.get_init.reset_mock()
    _pg_mixer.init.reset_mock()
    _pg_mixer.pause.reset_mock()
    _pg_mixer.unpause.reset_mock()
    _pg_mixer.stop.reset_mock()
    _pg_mixer.Sound   = MagicMock(side_effect=lambda path: _FakeSound(path))
    yield


@pytest.fixture()
def exists_true(monkeypatch):
    """os.path.exists retorna True para qualquer caminho."""
    monkeypatch.setattr("engine.audio.os.path.exists", lambda _: True)


@pytest.fixture()
def exists_false(monkeypatch):
    """os.path.exists retorna False para qualquer caminho."""
    monkeypatch.setattr("engine.audio.os.path.exists", lambda _: False)


# ── TestInit ─────────────────────────────────────────────────────────────────
class TestInit:
    def test_init_skipped_when_already_initialized(self):
        AudioManager._initialized = True
        result = AudioManager._init()
        assert result is True
        _pg_mixer.init.assert_not_called()

    def test_init_calls_mixer_init_when_not_initialized(self):
        AudioManager._initialized = False
        _pg_mixer.get_init.return_value = False
        AudioManager._init()
        _pg_mixer.init.assert_called_once()

    def test_init_skips_mixer_init_if_already_init(self):
        AudioManager._initialized = False
        _pg_mixer.get_init.return_value = True
        AudioManager._init()
        _pg_mixer.init.assert_not_called()

    def test_init_returns_false_on_exception(self, monkeypatch):
        AudioManager._initialized = False
        _pg_mixer.get_init.return_value = False
        _pg_mixer.init.side_effect = Exception("no audio")
        result = AudioManager._init()
        assert result is False
        _pg_mixer.init.side_effect = None  # reset


# ── TestPlayMusic ──────────────────────────────────────────────────────────────
class TestPlayMusic:
    def test_play_music_loads_path(self, exists_true):
        AudioManager.play_music("theme.ogg")
        _pg_mixer.music.load.assert_called_once_with("theme.ogg")

    def test_play_music_calls_play_loop(self, exists_true):
        AudioManager.play_music("theme.ogg", loop=True)
        _pg_mixer.music.play.assert_called_once_with(-1, fade_ms=0)

    def test_play_music_calls_play_no_loop(self, exists_true):
        AudioManager.play_music("theme.ogg", loop=False)
        _pg_mixer.music.play.assert_called_once_with(0, fade_ms=0)

    def test_play_music_with_fade(self, exists_true):
        AudioManager.play_music("theme.ogg", fade_ms=500)
        _pg_mixer.music.play.assert_called_once_with(-1, fade_ms=500)

    def test_play_music_stores_path(self, exists_true):
        AudioManager.play_music("theme.ogg")
        assert AudioManager._music_path == "theme.ogg"

    def test_play_music_clears_paused_flag(self, exists_true):
        AudioManager._music_paused = True
        AudioManager.play_music("theme.ogg")
        assert AudioManager._music_paused is False

    def test_play_music_skips_if_file_missing(self, exists_false):
        AudioManager.play_music("missing.ogg")
        _pg_mixer.music.load.assert_not_called()

    def test_play_music_sets_volume(self, exists_true):
        AudioManager._master_volume = 0.8
        AudioManager._music_volume  = 0.5
        AudioManager.play_music("theme.ogg")
        _pg_mixer.music.set_volume.assert_called_with(pytest.approx(0.4))


# ── TestStopMusic ──────────────────────────────────────────────────────────────
class TestStopMusic:
    def test_stop_music_calls_stop(self):
        AudioManager.stop_music()
        _pg_mixer.music.stop.assert_called_once()

    def test_stop_music_with_fade_calls_fadeout(self):
        AudioManager.stop_music(fade_ms=300)
        _pg_mixer.music.fadeout.assert_called_once_with(300)

    def test_stop_music_with_fade_does_not_call_stop(self):
        AudioManager.stop_music(fade_ms=300)
        _pg_mixer.music.stop.assert_not_called()

    def test_stop_music_clears_path(self):
        AudioManager._music_path = "theme.ogg"
        AudioManager.stop_music()
        assert AudioManager._music_path is None

    def test_stop_music_clears_paused_flag(self):
        AudioManager._music_paused = True
        AudioManager.stop_music()
        assert AudioManager._music_paused is False


# ── TestPauseResumeMusic ──────────────────────────────────────────────────────────
class TestPauseResumeMusic:
    def test_pause_calls_mixer_pause(self):
        AudioManager.pause_music()
        _pg_mixer.music.pause.assert_called_once()

    def test_pause_sets_paused_flag(self):
        AudioManager.pause_music()
        assert AudioManager._music_paused is True

    def test_pause_idempotent_if_already_paused(self):
        AudioManager._music_paused = True
        AudioManager.pause_music()
        _pg_mixer.music.pause.assert_not_called()

    def test_resume_calls_unpause(self):
        AudioManager._music_paused = True
        AudioManager.resume_music()
        _pg_mixer.music.unpause.assert_called_once()

    def test_resume_clears_paused_flag(self):
        AudioManager._music_paused = True
        AudioManager.resume_music()
        assert AudioManager._music_paused is False

    def test_resume_idempotent_if_not_paused(self):
        AudioManager._music_paused = False
        AudioManager.resume_music()
        _pg_mixer.music.unpause.assert_not_called()

    def test_is_music_playing_true(self):
        _pg_mixer.music.get_busy.return_value = True
        AudioManager._music_paused = False
        assert AudioManager.is_music_playing() is True

    def test_is_music_playing_false_when_paused(self):
        _pg_mixer.music.get_busy.return_value = True
        AudioManager._music_paused = True
        assert AudioManager.is_music_playing() is False

    def test_is_music_playing_false_when_not_busy(self):
        _pg_mixer.music.get_busy.return_value = False
        assert AudioManager.is_music_playing() is False


# ── TestMusicVolume ──────────────────────────────────────────────────────────────
class TestMusicVolume:
    def test_set_music_volume_clamps_max(self):
        AudioManager.set_music_volume(2.0)
        assert AudioManager._music_volume == pytest.approx(1.0)

    def test_set_music_volume_clamps_min(self):
        AudioManager.set_music_volume(-1.0)
        assert AudioManager._music_volume == pytest.approx(0.0)

    def test_set_music_volume_updates_mixer(self):
        AudioManager._master_volume = 1.0
        AudioManager.set_music_volume(0.6)
        _pg_mixer.music.set_volume.assert_called_with(pytest.approx(0.6))

    def test_set_music_volume_multiplied_by_master(self):
        AudioManager._master_volume = 0.5
        AudioManager.set_music_volume(0.8)
        _pg_mixer.music.set_volume.assert_called_with(pytest.approx(0.4))


# ── TestSfx ───────────────────────────────────────────────────────────────────
class TestSfx:
    def test_play_sfx_loads_sound(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        _pg_mixer.Sound.assert_called_once_with("jump.wav")

    def test_play_sfx_caches_sound(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        AudioManager.play_sfx("jump.wav")  # segunda chamada
        assert _pg_mixer.Sound.call_count == 1  # carregou apenas uma vez

    def test_play_sfx_calls_play(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        sound = AudioManager._sound_cache["jump.wav"]
        sound.play.assert_called_once_with(0)

    def test_play_sfx_sets_volume(self, exists_true):
        AudioManager._master_volume = 0.5
        AudioManager._sfx_volume    = 0.8
        AudioManager.play_sfx("jump.wav", volume=1.0)
        sound = AudioManager._sound_cache["jump.wav"]
        sound.set_volume.assert_called_with(pytest.approx(0.4))

    def test_play_sfx_volume_clamped_max(self, exists_true):
        AudioManager.play_sfx("jump.wav", volume=10.0)
        sound = AudioManager._sound_cache["jump.wav"]
        args = sound.set_volume.call_args[0][0]
        assert args <= 1.0

    def test_play_sfx_returns_channel(self, exists_true):
        ch = AudioManager.play_sfx("jump.wav")
        assert ch is not None

    def test_play_sfx_returns_none_if_missing(self, exists_false):
        ch = AudioManager.play_sfx("missing.wav")
        assert ch is None

    def test_play_sfx_loops_param(self, exists_true):
        AudioManager.play_sfx("jump.wav", loops=-1)
        sound = AudioManager._sound_cache["jump.wav"]
        sound.play.assert_called_once_with(-1)

    def test_stop_sfx_calls_sound_stop(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        AudioManager.stop_sfx("jump.wav")
        sound = AudioManager._sound_cache["jump.wav"]
        sound.stop.assert_called_once()

    def test_stop_sfx_noop_if_not_cached(self):
        AudioManager.stop_sfx("never_played.wav")  # não deve lançar

    def test_set_sfx_volume_updates_cache(self, exists_true):
        AudioManager.play_sfx("a.wav")
        AudioManager.play_sfx("b.wav") if "b.wav" != "a.wav" else None
        AudioManager.set_sfx_volume(0.3)
        assert AudioManager._sfx_volume == pytest.approx(0.3)

    def test_set_sfx_volume_clamps_max(self):
        AudioManager.set_sfx_volume(5.0)
        assert AudioManager._sfx_volume == pytest.approx(1.0)

    def test_set_sfx_volume_clamps_min(self):
        AudioManager.set_sfx_volume(-1.0)
        assert AudioManager._sfx_volume == pytest.approx(0.0)


# ── TestMasterVolume ─────────────────────────────────────────────────────────────
class TestMasterVolume:
    def test_set_master_volume_stored(self):
        AudioManager.set_master_volume(0.4)
        assert AudioManager._master_volume == pytest.approx(0.4)

    def test_set_master_volume_clamps_max(self):
        AudioManager.set_master_volume(3.0)
        assert AudioManager._master_volume == pytest.approx(1.0)

    def test_set_master_volume_clamps_min(self):
        AudioManager.set_master_volume(-1.0)
        assert AudioManager._master_volume == pytest.approx(0.0)

    def test_set_master_volume_updates_music(self):
        AudioManager._music_volume = 0.5
        AudioManager.set_master_volume(0.8)
        _pg_mixer.music.set_volume.assert_called_with(pytest.approx(0.4))

    def test_set_master_volume_updates_sfx_cache(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        sound = AudioManager._sound_cache["jump.wav"]
        sound.set_volume.reset_mock()
        AudioManager._sfx_volume = 0.5
        AudioManager.set_master_volume(0.4)
        sound.set_volume.assert_called_with(pytest.approx(0.2))

    def test_set_master_zero_silences_all(self, exists_true):
        AudioManager.play_sfx("jump.wav")
        sound = AudioManager._sound_cache["jump.wav"]
        sound.set_volume.reset_mock()
        AudioManager.set_master_volume(0.0)
        sound.set_volume.assert_called_with(pytest.approx(0.0))


# ── TestGlobalControl ────────────────────────────────────────────────────────────
class TestGlobalControl:
    def test_pause_all_pauses_music(self):
        AudioManager.pause_all()
        _pg_mixer.music.pause.assert_called_once()

    def test_pause_all_pauses_mixer(self):
        AudioManager.pause_all()
        _pg_mixer.pause.assert_called_once()

    def test_resume_all_resumes_music(self):
        AudioManager._music_paused = True
        AudioManager.resume_all()
        _pg_mixer.music.unpause.assert_called_once()

    def test_resume_all_resumes_mixer(self):
        AudioManager._music_paused = True
        AudioManager.resume_all()
        _pg_mixer.unpause.assert_called_once()

    def test_stop_all_stops_music(self):
        AudioManager.stop_all()
        _pg_mixer.music.stop.assert_called_once()

    def test_stop_all_stops_mixer(self):
        AudioManager.stop_all()
        _pg_mixer.stop.assert_called_once()

    def test_stop_all_clears_music_path(self):
        AudioManager._music_path = "theme.ogg"
        AudioManager.stop_all()
        assert AudioManager._music_path is None


# ── TestUnloadCache ─────────────────────────────────────────────────────────────
class TestUnloadCache:
    def test_unload_cache_stops_all_sounds(self, exists_true):
        AudioManager.play_sfx("a.wav")
        AudioManager.play_sfx("b.wav")
        sounds = list(AudioManager._sound_cache.values())
        AudioManager.unload_cache()
        for s in sounds:
            s.stop.assert_called_once()

    def test_unload_cache_clears_dict(self, exists_true):
        AudioManager.play_sfx("a.wav")
        AudioManager.unload_cache()
        assert AudioManager._sound_cache == {}

    def test_unload_cache_noop_when_empty(self):
        AudioManager.unload_cache()  # sem crash
        assert AudioManager._sound_cache == {}
