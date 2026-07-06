from __future__ import annotations

from engine.audio import AudioSource
from engine.graphics.camera import Camera
from engine.runtime import Input, ScriptBehaviour


class Script(ScriptBehaviour):
    """Reference player movement script for Zennity Runtime.

    The Runtime accepts either a class named Script or any ScriptBehaviour
    subclass. Using Script keeps examples consistent and explicit.
    """

    speed = 120.0

    def on_start(self) -> None:
        print(f"[GettingStarted] {self.game_object.name} started")
        if Camera.main:
            print(f"[GettingStarted] Main Camera zoom: {Camera.main.zoom}")

    def on_update(self, delta_time: float) -> None:
        if self.transform is None:
            return

        direction = 0.0
        if Input.is_key_down("A") or Input.is_key_down("Left"):
            direction -= 1.0
        if Input.is_key_down("D") or Input.is_key_down("Right"):
            direction += 1.0
        if Input.is_key_down("Space"):
            direction += 1.0

        if direction == 0.0:
            return

        self.transform.position[0] += direction * self.speed * float(delta_time)
        source = self.get_component(AudioSource)
        if source and not source.is_playing():
            source.play()

    def on_destroy(self) -> None:
        print(f"[GettingStarted] {self.game_object.name} stopped")
