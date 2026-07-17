from __future__ import annotations

from typing import Any

from engine.input import Input


class ScriptBehaviour:
    """Base class for Python scripts executed by the Runtime World."""

    def __init__(self) -> None:
        self.game_object: Any | None = None
        self.runtime: Any | None = None
        self.scene: Any | None = None
        self.input = Input

    @property
    def transform(self) -> Any:
        return self.game_object.transform if self.game_object is not None else None

    def get_component(self, component_type: type) -> Any | None:
        if self.game_object is None:
            return None
        return self.game_object.get_component(component_type)

    def on_awake(self) -> None:
        """Called after the script instance is bound to a Runtime GameObject."""

    def on_start(self) -> None:
        """Called once after on_awake when Play Mode starts."""

    def on_update(self, delta_time: float) -> None:
        """Called on each RuntimeManager.tick(delta_time)."""

    def on_destroy(self) -> None:
        """Called when Play Mode stops and the Runtime World is destroyed."""

    def on_trigger_enter(self, other: Any) -> None:
        """Called when this GameObject enters a trigger contact."""

    def on_trigger_exit(self, other: Any) -> None:
        """Called when this GameObject exits a trigger contact."""

    def on_collision_enter(self, other: Any) -> None:
        """Reserved for future collision events."""
