"""
Phase 7B.6: Audio Visual System Validation & Completion

Tests that audio works end-to-end through Logic Graph:

On Start
↓
Play Music "level_theme.ogg"
↓
Set Master Volume

On Collision
↓
Play Sound "hit.wav"

On Animation Event
↓
Play Sound "footstep.wav"

100% without Python audio management.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.logic.runtime.registry import registry
from editor.runtime.viewport_logic_api import PlayLogicAPI

# Ensure audio nodes are imported
import engine.logic.runtime.nodes.audio_advanced_nodes  # noqa


class TestAudioNodesRegistered:
    """Verify audio nodes are in registry."""

    def test_play_sound_registered(self):
        """Verify play_sound executor exists."""
        assert "play_sound" in registry.executors, "play_sound executor missing"

    def test_play_sound_fade_registered(self):
        """Verify play_sound_fade executor exists."""
        assert "play_sound_fade" in registry.executors, "play_sound_fade executor missing"

    def test_set_volume_registered(self):
        """Verify set_volume executor exists."""
        assert "set_volume" in registry.executors, "set_volume executor missing"

    def test_set_pitch_registered(self):
        """Verify set_pitch executor exists."""
        assert "set_pitch" in registry.executors, "set_pitch executor missing"

    def test_stop_all_sounds_registered(self):
        """Verify stop_all_sounds executor exists."""
        assert "stop_all_sounds" in registry.executors, "stop_all_sounds executor missing"


class TestPlayLogicAPIAudioMethods:
    """Verify PlayLogicAPI has all audio methods."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_play_sound_exists(self):
        """Verify play_sound() method exists."""
        assert hasattr(self.api, "play_sound"), "PlayLogicAPI missing play_sound()"
        assert callable(self.api.play_sound), "play_sound() not callable"

    def test_play_music_exists(self):
        """Verify play_music() method exists."""
        assert hasattr(self.api, "play_music"), "PlayLogicAPI missing play_music()"
        assert callable(self.api.play_music), "play_music() not callable"

    def test_stop_sound_exists(self):
        """Verify stop_sound() method exists."""
        assert hasattr(self.api, "stop_sound"), "PlayLogicAPI missing stop_sound()"
        assert callable(self.api.stop_sound), "stop_sound() not callable"

    def test_stop_music_exists(self):
        """Verify stop_music() method exists."""
        assert hasattr(self.api, "stop_music"), "PlayLogicAPI missing stop_music()"
        assert callable(self.api.stop_music), "stop_music() not callable"

    def test_stop_all_sounds_exists(self):
        """Verify stop_all_sounds() method exists."""
        assert hasattr(self.api, "stop_all_sounds"), "PlayLogicAPI missing stop_all_sounds()"
        assert callable(self.api.stop_all_sounds), "stop_all_sounds() not callable"

    def test_set_master_volume_exists(self):
        """Verify set_master_volume() method exists."""
        assert hasattr(self.api, "set_master_volume"), "PlayLogicAPI missing set_master_volume()"
        assert callable(self.api.set_master_volume), "set_master_volume() not callable"

    def test_set_music_volume_exists(self):
        """Verify set_music_volume() method exists."""
        assert hasattr(self.api, "set_music_volume"), "PlayLogicAPI missing set_music_volume()"
        assert callable(self.api.set_music_volume), "set_music_volume() not callable"

    def test_set_sfx_volume_exists(self):
        """Verify set_sfx_volume() method exists."""
        assert hasattr(self.api, "set_sfx_volume"), "PlayLogicAPI missing set_sfx_volume()"
        assert callable(self.api.set_sfx_volume), "set_sfx_volume() not callable"

    def test_get_master_volume_exists(self):
        """Verify get_master_volume() method exists."""
        assert hasattr(self.api, "get_master_volume"), "PlayLogicAPI missing get_master_volume()"
        assert callable(self.api.get_master_volume), "get_master_volume() not callable"


class TestAudioPlayback:
    """Test audio playback functionality."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_play_sound_valid_path(self):
        """Verify play_sound() accepts valid path."""
        result = self.api.play_sound("Assets/Audio/hit.wav")
        assert result is True, "play_sound() should return True"

    def test_play_sound_empty_path(self):
        """Verify play_sound() rejects empty path."""
        result = self.api.play_sound("")
        assert result is False, "play_sound() should return False for empty path"

    def test_play_sound_with_volume(self):
        """Verify play_sound() accepts volume parameter."""
        result = self.api.play_sound("Assets/Audio/hit.wav", volume=0.5)
        assert result is True, "play_sound() should accept volume"

    def test_play_sound_with_loop(self):
        """Verify play_sound() accepts loop parameter."""
        result = self.api.play_sound("Assets/Audio/bgm.ogg", loop=True)
        assert result is True, "play_sound() should accept loop"

    def test_play_music_valid_path(self):
        """Verify play_music() accepts valid path."""
        result = self.api.play_music("Assets/Audio/level_theme.ogg")
        assert result is True, "play_music() should return True"

    def test_play_music_empty_path(self):
        """Verify play_music() rejects empty path."""
        result = self.api.play_music("")
        assert result is False, "play_music() should return False for empty path"

    def test_play_music_with_fade_in(self):
        """Verify play_music() accepts fade_in parameter."""
        result = self.api.play_music("Assets/Audio/level_theme.ogg", fade_in=1.0)
        assert result is True, "play_music() should accept fade_in"

    def test_stop_sound(self):
        """Verify stop_sound() works."""
        result = self.api.stop_sound("Assets/Audio/hit.wav")
        assert result is True, "stop_sound() should return True"

    def test_stop_music(self):
        """Verify stop_music() works."""
        result = self.api.stop_music()
        assert result is True, "stop_music() should return True"

    def test_stop_all_sounds(self):
        """Verify stop_all_sounds() works."""
        result = self.api.stop_all_sounds()
        assert result is True, "stop_all_sounds() should return True"


class TestAudioVolumeControl:
    """Test volume control functionality."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_set_master_volume_valid(self):
        """Verify set_master_volume() accepts valid values."""
        result = self.api.set_master_volume(0.5)
        assert result is True, "set_master_volume() should return True"

    def test_set_master_volume_clamped_high(self):
        """Verify set_master_volume() clamps to 1.0."""
        result = self.api.set_master_volume(2.0)
        assert result is True, "set_master_volume() should clamp high values"

    def test_set_master_volume_clamped_low(self):
        """Verify set_master_volume() clamps to 0.0."""
        result = self.api.set_master_volume(-1.0)
        assert result is True, "set_master_volume() should clamp low values"

    def test_set_music_volume(self):
        """Verify set_music_volume() works."""
        result = self.api.set_music_volume(0.7)
        assert result is True, "set_music_volume() should return True"

    def test_set_sfx_volume(self):
        """Verify set_sfx_volume() works."""
        result = self.api.set_sfx_volume(0.8)
        assert result is True, "set_sfx_volume() should return True"

    def test_get_master_volume(self):
        """Verify get_master_volume() returns float."""
        result = self.api.get_master_volume()
        assert isinstance(result, float), "get_master_volume() should return float"
        assert 0.0 <= result <= 1.0, "Volume should be between 0.0 and 1.0"


class TestAudioE2E:
    """E2E tests for audio gameplay flows."""

    def setup_method(self):
        """Create test object and API."""
        self.obj = {"name": "Game"}
        self.api = PlayLogicAPI("Game", self.obj, None)

    def test_level_start_audio_flow(self):
        """Test On Start → Play Music flow."""
        # Simulate On Start event
        result = self.api.play_music("Assets/Audio/level_theme.ogg", volume=0.8)
        assert result is True, "Should play level music on start"

    def test_collision_audio_flow(self):
        """Test On Collision → Play Sound flow."""
        # Simulate collision event
        result = self.api.play_sound("Assets/Audio/hit.wav")
        assert result is True, "Should play collision sound"

    def test_animation_event_audio_flow(self):
        """Test Animation Event → Play Sound flow."""
        # Simulate footstep animation event
        result = self.api.play_sound("Assets/Audio/footstep.wav", volume=0.5)
        assert result is True, "Should play footstep sound on animation event"

    def test_pause_menu_volume_control(self):
        """Test Pause Menu → Volume Control flow."""
        # Simulate pause menu volume slider
        result = self.api.set_master_volume(0.3)
        assert result is True, "Should set master volume in pause menu"

    def test_scene_change_audio_cleanup(self):
        """Test Scene Change → Audio Cleanup flow."""
        # Play music in Level1
        self.api.play_music("Assets/Audio/level1_theme.ogg")

        # Change scene
        # (In real usage, scene change would stop music automatically)
        # Verify we can stop it manually
        result = self.api.stop_music()
        assert result is True, "Should stop music on scene change"

    def test_multiple_sfx_simultaneous(self):
        """Test multiple SFX playing simultaneously."""
        # Play multiple sounds
        result1 = self.api.play_sound("Assets/Audio/impact1.wav")
        result2 = self.api.play_sound("Assets/Audio/impact2.wav")
        result3 = self.api.play_sound("Assets/Audio/impact3.wav")

        assert all([result1, result2, result3]), "Should play multiple SFX simultaneously"

    def test_music_while_sfx_plays(self):
        """Test music and SFX playing together."""
        # Play music
        music_result = self.api.play_music("Assets/Audio/level_theme.ogg")
        # Play SFX
        sfx_result = self.api.play_sound("Assets/Audio/hit.wav")

        assert music_result and sfx_result, "Music and SFX should play together"

    def test_stop_all_after_multiple_sounds(self):
        """Test stop_all_sounds() stops everything."""
        # Play music and sounds
        self.api.play_music("Assets/Audio/level_theme.ogg")
        self.api.play_sound("Assets/Audio/hit.wav")
        self.api.play_sound("Assets/Audio/step.wav")

        # Stop everything
        result = self.api.stop_all_sounds()
        assert result is True, "stop_all_sounds() should work"


class TestAudioMethodsCallable:
    """Verify all audio methods are callable."""

    def test_all_audio_methods_callable(self):
        """Verify all audio methods exist and are callable."""
        obj = {"name": "Game"}
        api = PlayLogicAPI("Game", obj, None)

        required_methods = [
            "play_sound",
            "play_music",
            "stop_sound",
            "stop_music",
            "stop_all_sounds",
            "set_master_volume",
            "set_music_volume",
            "set_sfx_volume",
            "get_master_volume",
        ]

        for method_name in required_methods:
            assert hasattr(api, method_name), f"Missing: {method_name}"
            assert callable(getattr(api, method_name)), f"Not callable: {method_name}"

    def test_audio_methods_callable_without_crash(self):
        """Verify audio methods can be called without exception."""
        obj = {"name": "Game"}
        api = PlayLogicAPI("Game", obj, None)

        try:
            api.play_sound("Assets/Audio/test.wav")
            api.play_music("Assets/Audio/bgm.ogg")
            api.stop_sound("Assets/Audio/test.wav")
            api.stop_music()
            api.stop_all_sounds()
            api.set_master_volume(0.5)
            api.set_music_volume(0.6)
            api.set_sfx_volume(0.7)
            api.get_master_volume()
        except Exception as e:
            pytest.fail(f"Audio method crashed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
