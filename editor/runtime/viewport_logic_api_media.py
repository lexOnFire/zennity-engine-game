"""Animation, audio and sprite helpers for PlayLogicAPI."""
from __future__ import annotations

from pathlib import Path

try:
    from engine.animation.clip_asset import animation_asset_to_clip, load_animation_asset
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .clip_asset import animation_asset_to_clip, load_animation_asset


class PlayMediaMixin:
    def play_animation_asset(self, asset_path: str) -> None:
        """Carrega e inicia um ``.zanim`` durante o Play Mode."""
        path = Path(str(asset_path))
        if not path.is_absolute():
            path = Path.cwd() / path
        asset = load_animation_asset(path)
        relative = path.relative_to(Path.cwd()).as_posix() if path.is_relative_to(Path.cwd()) else str(path)
        clip = animation_asset_to_clip(asset, relative)
        name = str(asset.get("name", path.stem))
        animator = self.obj.setdefault("animator", {"active_clip": name, "speed": 1.0, "clips": {}})
        animator.setdefault("clips", {})[name] = clip
        animator["active_clip"] = name
        self.obj["_current_animation_name"] = name
        self.obj["_animation_time"] = 0.0
        self.obj["_animation_frame"] = 0
        self.obj["_animation_raw_frame"] = -1

    def play_sound(self, sound_path: str, volume: float = 1.0, loop: bool = False) -> bool:
        """Play a sound effect."""
        if not sound_path:
            return False
        self.send("play_sound", {
            "path": str(sound_path),
            "volume": float(volume),
            "loop": bool(loop)
        })
        return True

    def play_music(self, music_path: str, volume: float = 1.0, loop: bool = True, fade_in: float = 0.0) -> bool:
        """Play background music."""
        if not music_path:
            return False
        self.send("play_music", {
            "path": str(music_path),
            "volume": float(volume),
            "loop": bool(loop),
            "fade_in": float(fade_in)
        })
        return True

    def stop_sound(self, sound_path: str = None) -> bool:
        """Stop a playing sound."""
        self.send("stop_sound", {"path": str(sound_path) if sound_path else None})
        return True

    def stop_music(self, fade_out: float = 0.0) -> bool:
        """Stop background music."""
        self.send("stop_music", {"fade_out": float(fade_out)})
        return True

    def stop_all_sounds(self) -> bool:
        """Stop all audio playback."""
        self.send("stop_all_sounds")
        return True

    def set_master_volume(self, volume: float) -> bool:
        """Set master volume level (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, float(volume)))
        self.send("set_master_volume", {"volume": volume})
        return True

    def set_music_volume(self, volume: float) -> bool:
        """Set music volume level (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, float(volume)))
        self.send("set_music_volume", {"volume": volume})
        return True

    def set_sfx_volume(self, volume: float) -> bool:
        """Set SFX volume level (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, float(volume)))
        self.send("set_sfx_volume", {"volume": volume})
        return True

    def get_master_volume(self) -> float:
        """Get current master volume (pure getter)."""
        try:
            from engine.audio import AudioManager
            manager = AudioManager.get_instance()
            return manager.get_master_volume() if manager else 1.0
        except Exception:
            return 1.0

    def set_sprite(self, image_path: str) -> None:
        """Troca a textura principal do objeto sem recriá-lo."""
        self.obj["texture"] = str(image_path)
        self.obj["renderer_enabled"] = True

    def start_texture_scroll(
        self,
        speed_x: float = 0.0,
        speed_y: float = 80.0,
        *,
        repeat_x: bool = False,
        repeat_y: bool = True,
        parallax: float = 1.0,
        image_path: str = "",
        send_to_background: bool = True,
    ) -> None:
        """Inicia uma textura repetida no plano sem mover o objeto físico."""
        if image_path:
            self.set_sprite(image_path)
        if send_to_background:
            self.obj["render_layer"] = "Background"
        previous = self.obj.get("_texture_scroll")
        state = previous if isinstance(previous, dict) else {}
        state.update({
            "enabled": True,
            "speed_x": float(speed_x),
            "speed_y": float(speed_y),
            "repeat_x": bool(repeat_x),
            "repeat_y": bool(repeat_y),
            "parallax": max(0.0, float(parallax)),
        })
        state.setdefault("offset_x", 0.0)
        state.setdefault("offset_y", 0.0)
        self.obj["_texture_scroll"] = state

    def stop_texture_scroll(self, reset: bool = False) -> None:
        """Interrompe o fundo rolante; opcionalmente retorna à origem."""
        state = self.obj.get("_texture_scroll")
        if not isinstance(state, dict):
            return
        state["enabled"] = False
        if reset:
            state["offset_x"] = 0.0
            state["offset_y"] = 0.0

