from __future__ import annotations

from engine.runtime import Input, ScriptBehaviour


class Script(ScriptBehaviour):
    """Reference script showing safe mouse input usage."""

    def on_update(self, delta_time: float) -> None:
        if Input.is_mouse_pressed(1) or Input.is_mouse_pressed("left"):
            print(f"[ClickLogger] Mouse clicked at {Input.mouse_position()}")
