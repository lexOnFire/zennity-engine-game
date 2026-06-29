import pygame
from .assets import Assets
from typing import Dict

class Audio:
    """Centralized manager for audio playback in the engine."""
    
    @staticmethod
    def play_sound(path: str, volume: float = 1.0) -> pygame.mixer.Channel:
        """Plays a sound effect once and returns the playback channel."""
        snd = Assets.get_sound(path)
        snd.set_volume(volume)
        return snd.play()

    @staticmethod
    def play_music(path: str, loops: int = -1, volume: float = 0.5) -> None:
        """Loads and plays background music streaming."""
        Assets.play_music(path, loops, volume)

    @staticmethod
    def stop_music() -> None:
        """Stops background music."""
        pygame.mixer.music.stop()

    @staticmethod
    def pause_music() -> None:
        """Pauses background music."""
        pygame.mixer.music.pause()

    @staticmethod
    def unpause_music() -> None:
        """Resumes paused background music."""
        pygame.mixer.music.unpause()

    @staticmethod
    def set_music_volume(volume: float) -> None:
        """Sets background music volume (0.0 to 1.0)."""
        pygame.mixer.music.set_volume(volume)
