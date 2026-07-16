"""Serviços de execução independentes usados pela Viewport isolada.

Não importam a janela do editor e podem ser testados sem iniciar Qt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class FixedStepScheduler:
    """Converte delta variável em uma quantidade limitada de passos fixos."""

    def __init__(self, step: float = 1.0 / 60.0, maximum_steps: int = 5) -> None:
        self.step = max(0.000001, float(step))
        self.maximum_steps = max(1, int(maximum_steps))
        self.accumulator = 0.0

    def reset(self) -> None:
        self.accumulator = 0.0

    def consume(self, delta_time: float) -> int:
        self.accumulator = min(
            self.accumulator + max(0.0, float(delta_time)),
            self.step * self.maximum_steps,
        )
        count = min(int(self.accumulator / self.step), self.maximum_steps)
        self.accumulator -= count * self.step
        return count


class HudRuntimeSystem(dict[str, dict[str, Any]]):
    """Estado isolado do HUD, com API explícita para comandos visuais."""

    def set_entry(self, value: dict[str, Any]) -> None:
        self[str(value.get("key", "default"))] = dict(value)

    def remove_entry(self, key: str) -> None:
        self.pop(str(key), None)

    def grouped(self) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for entry in self.values():
            groups.setdefault(str(entry.get("position", "top-left")), []).append(entry)
        return groups


@dataclass(frozen=True)
class AnimationFrameResult:
    elapsed: float
    raw_frame: int
    frame: int
    crossed_frames: tuple[int, ...]


class AnimationPlaybackSystem:
    """Calcula frames e eventos atravessados sem conhecer scripts ou Pygame."""

    @staticmethod
    def advance(
        elapsed: float,
        previous_raw: int,
        delta_time: float,
        frame_count: int,
        fps: float,
        loop: bool,
    ) -> AnimationFrameResult:
        count = max(1, int(frame_count))
        elapsed = float(elapsed) + max(0.0, float(delta_time))
        raw_frame = int(elapsed * max(0.0, float(fps)))
        frame = raw_frame % count if loop else min(count - 1, raw_frame)
        crossed: list[int] = []
        if raw_frame > int(previous_raw):
            upper = min(raw_frame, int(previous_raw) + max(1, count * 4))
            seen: set[int] = set()
            for raw_index in range(int(previous_raw) + 1, upper + 1):
                event_frame = raw_index % count if loop else min(count - 1, raw_index)
                if not loop and event_frame in seen:
                    continue
                seen.add(event_frame)
                crossed.append(event_frame)
        return AnimationFrameResult(elapsed, raw_frame, frame, tuple(crossed))


class AudioPlaybackSystem:
    """Controla mixer, sons e canais sem conhecer o loop da Viewport."""

    def __init__(self, pygame_module: Any, project_root: Path, log: Callable[[str, str], None]) -> None:
        self.pygame = pygame_module
        self.project_root = Path(project_root)
        self.log = log
        self.channels: dict[str, Any] = {}
        self.sounds: dict[str, Any] = {}

    def ensure_mixer(self) -> bool:
        try:
            if not self.pygame.mixer.get_init():
                self.pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.pygame.mixer.set_num_channels(max(16, self.pygame.mixer.get_num_channels()))
            return True
        except self.pygame.error as exc:
            self.log("WARNING", f"Áudio indisponível: {exc}")
            return False

    def play(self, key: str, path_value: str, volume: float = 1.0, loop: bool = False) -> None:
        path = Path(str(path_value))
        if not path.is_absolute():
            path = self.project_root / path
        if not path.is_file():
            self.log("ERROR", f"{key}: arquivo de áudio não encontrado: {path_value}")
            return
        if not self.ensure_mixer():
            return
        try:
            previous = self.channels.pop(key, None)
            if previous is not None:
                previous.stop()
            sound = self.pygame.mixer.Sound(str(path.resolve()))
            sound.set_volume(max(0.0, min(1.0, float(volume))))
            channel = sound.play(loops=-1 if loop else 0)
            if channel is None:
                self.log("WARNING", f"{key}: nenhum canal de áudio disponível")
                return
            self.sounds[key] = sound
            self.channels[key] = channel
            self.log("INFO", f"Áudio tocando: {path.name} (volume {sound.get_volume():.2f})")
        except (OSError, self.pygame.error) as exc:
            self.log("ERROR", f"{key}: falha ao tocar {path.name}: {exc}")

    def stop_all(self) -> None:
        for channel in self.channels.values():
            try:
                channel.stop()
            except self.pygame.error:
                pass
        self.channels.clear()
        self.sounds.clear()
        if self.pygame.mixer.get_init():
            self.pygame.mixer.stop()
            try:
                self.pygame.mixer.music.stop()
            except self.pygame.error:
                pass

