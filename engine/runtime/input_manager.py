from __future__ import annotations

from typing import Any


class InputManager:
    """Backend-neutral input state used only by the Runtime World."""

    def __init__(self) -> None:
        self.active = False
        self._keys_down: set[str] = set()
        self._keys_pressed: set[str] = set()
        self._keys_released: set[str] = set()
        self._pending_keys_pressed: set[str] = set()
        self._pending_keys_released: set[str] = set()

        self._mouse_down: set[int] = set()
        self._mouse_pressed: set[int] = set()
        self._mouse_released: set[int] = set()
        self._pending_mouse_pressed: set[int] = set()
        self._pending_mouse_released: set[int] = set()

        self._mouse_position: tuple[float, float] = (0.0, 0.0)
        self._last_mouse_position: tuple[float, float] = (0.0, 0.0)
        self._mouse_delta: tuple[float, float] = (0.0, 0.0)
        self._pending_mouse_delta: tuple[float, float] = (0.0, 0.0)

    def start(self) -> None:
        self.clear()
        self.active = True

    def stop(self) -> None:
        self.clear()
        self.active = False

    def clear(self) -> None:
        self._keys_down.clear()
        self._keys_pressed.clear()
        self._keys_released.clear()
        self._pending_keys_pressed.clear()
        self._pending_keys_released.clear()
        self._mouse_down.clear()
        self._mouse_pressed.clear()
        self._mouse_released.clear()
        self._pending_mouse_pressed.clear()
        self._pending_mouse_released.clear()
        self._mouse_position = (0.0, 0.0)
        self._last_mouse_position = (0.0, 0.0)
        self._mouse_delta = (0.0, 0.0)
        self._pending_mouse_delta = (0.0, 0.0)

    def update(self) -> None:
        if not self.active:
            self._keys_pressed.clear()
            self._keys_released.clear()
            self._mouse_pressed.clear()
            self._mouse_released.clear()
            self._mouse_delta = (0.0, 0.0)
            return

        self._keys_pressed = set(self._pending_keys_pressed)
        self._keys_released = set(self._pending_keys_released)
        self._pending_keys_pressed.clear()
        self._pending_keys_released.clear()

        self._mouse_pressed = set(self._pending_mouse_pressed)
        self._mouse_released = set(self._pending_mouse_released)
        self._pending_mouse_pressed.clear()
        self._pending_mouse_released.clear()

        self._mouse_delta = self._pending_mouse_delta
        self._pending_mouse_delta = (0.0, 0.0)

    def key_down(self, key: Any) -> None:
        if not self.active:
            return
        normalized = self.normalize_key(key)
        if normalized not in self._keys_down:
            self._pending_keys_pressed.add(normalized)
        self._keys_down.add(normalized)
        self._pending_keys_released.discard(normalized)

    def key_up(self, key: Any) -> None:
        if not self.active:
            return
        normalized = self.normalize_key(key)
        if normalized in self._keys_down:
            self._pending_keys_released.add(normalized)
        self._keys_down.discard(normalized)
        self._pending_keys_pressed.discard(normalized)

    def mouse_down(self, button: Any) -> None:
        if not self.active:
            return
        normalized = self.normalize_mouse_button(button)
        if normalized not in self._mouse_down:
            self._pending_mouse_pressed.add(normalized)
        self._mouse_down.add(normalized)
        self._pending_mouse_released.discard(normalized)

    def mouse_up(self, button: Any) -> None:
        if not self.active:
            return
        normalized = self.normalize_mouse_button(button)
        if normalized in self._mouse_down:
            self._pending_mouse_released.add(normalized)
        self._mouse_down.discard(normalized)
        self._pending_mouse_pressed.discard(normalized)

    def set_mouse_position(self, x: float, y: float) -> None:
        if not self.active:
            return
        new_position = (float(x), float(y))
        dx = new_position[0] - self._mouse_position[0]
        dy = new_position[1] - self._mouse_position[1]
        self._last_mouse_position = self._mouse_position
        self._mouse_position = new_position
        self._pending_mouse_delta = (
            self._pending_mouse_delta[0] + dx,
            self._pending_mouse_delta[1] + dy,
        )

    def handle_event(self, event: Any) -> None:
        event_type = str(getattr(event, "type", "")).lower()
        if event_type in {"key_down", "keydown"}:
            self.key_down(getattr(event, "key", ""))
        elif event_type in {"key_up", "keyup"}:
            self.key_up(getattr(event, "key", ""))
        elif event_type in {"mouse_down", "mousebuttondown"}:
            self.set_mouse_position(*getattr(event, "pos", self._mouse_position))
            self.mouse_down(getattr(event, "button", 0))
        elif event_type in {"mouse_up", "mousebuttonup"}:
            self.set_mouse_position(*getattr(event, "pos", self._mouse_position))
            self.mouse_up(getattr(event, "button", 0))
        elif event_type in {"mouse_move", "mousemove", "mousemotion"}:
            self.set_mouse_position(*getattr(event, "pos", self._mouse_position))

    def is_key_down(self, key: Any) -> bool:
        return self.active and self.normalize_key(key) in self._keys_down

    def is_key_pressed(self, key: Any) -> bool:
        return self.active and self.normalize_key(key) in self._keys_pressed

    def is_key_released(self, key: Any) -> bool:
        return self.active and self.normalize_key(key) in self._keys_released

    def is_mouse_down(self, button: Any) -> bool:
        return self.active and self.normalize_mouse_button(button) in self._mouse_down

    def is_mouse_pressed(self, button: Any) -> bool:
        return self.active and self.normalize_mouse_button(button) in self._mouse_pressed

    def is_mouse_released(self, button: Any) -> bool:
        return self.active and self.normalize_mouse_button(button) in self._mouse_released

    def mouse_position(self) -> tuple[float, float]:
        return self._mouse_position if self.active else (0.0, 0.0)

    def mouse_delta(self) -> tuple[float, float]:
        return self._mouse_delta if self.active else (0.0, 0.0)

    @staticmethod
    def normalize_key(key: Any) -> str:
        if isinstance(key, str):
            return key.strip().lower()
        return str(key).strip().lower()

    @staticmethod
    def normalize_mouse_button(button: Any) -> int:
        if isinstance(button, str):
            aliases = {
                "left": 1,
                "middle": 2,
                "right": 3,
            }
            return aliases.get(button.strip().lower(), 0)
        try:
            return int(button)
        except (TypeError, ValueError):
            return 0
