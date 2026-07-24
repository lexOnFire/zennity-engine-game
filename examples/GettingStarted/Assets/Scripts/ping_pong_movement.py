from __future__ import annotations

from engine.runtime import ScriptBehaviour


class Script(ScriptBehaviour):
    """Reference script for simple horizontal ping-pong movement."""

    speed = 80.0
    distance = 120.0

    def on_awake(self) -> None:
        self._origin_x = float(self.transform.position[0]) if self.transform is not None else 0.0
        self._direction = 1.0

    def on_update(self, delta_time: float) -> None:
        if self.transform is None:
            return
        self.transform.position[0] += self._direction * self.speed * float(delta_time)
        offset = float(self.transform.position[0]) - self._origin_x
        if abs(offset) >= self.distance:
            self._direction *= -1.0
