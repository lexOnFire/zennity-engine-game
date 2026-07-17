from __future__ import annotations

from engine.runtime import ScriptBehaviour


class Script(ScriptBehaviour):
    """Reference script that rotates the GameObject every frame."""

    degrees_per_second = 90.0

    def on_update(self, delta_time: float) -> None:
        if self.transform is None:
            return
        self.transform.rotation[2] += self.degrees_per_second * float(delta_time)
