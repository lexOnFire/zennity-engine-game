"""Mixin para gerenciar movimentação persistente no runtime do Logic Graph."""

from __future__ import annotations

import math
from typing import Any, Mapping


class LogicGraphMotionMixin:
    """Mixin que isola a lógica de interpolação e movimentação contínua de alvos."""

    def _move_target(self, target: Any, velocity_x: float, velocity_y: float, dt: float) -> None:
        delta_x, delta_y = velocity_x * dt, velocity_y * dt
        if callable(getattr(target, "move", None)):
            target.move(delta_x, delta_y)
        else:
            target.x = float(target.x) + delta_x
            target.y = float(target.y) + delta_y
        override_physics = getattr(target, "override_physics_axis", None)
        if callable(override_physics):
            if velocity_x:
                override_physics("x")
            if velocity_y:
                override_physics("y")

    def _apply_persistent_motion(self, dt: float) -> None:
        for key, state in list(self._persistent_motion.items()):
            target = state.get("target")
            if target is None or not bool(getattr(target, "active", True)):
                self._persistent_motion.pop(key, None)
                self._remove_motion_debug(target, key)
                continue
            paused = bool(state.get("paused", False))
            stopping = bool(state.get("stopping", False))
            desired_x = 0.0 if paused or stopping else float(state.get("desired_x", 0.0))
            desired_y = 0.0 if paused or stopping else float(state.get("desired_y", 0.0))
            rate = float(state.get("deceleration" if paused or stopping else "acceleration", 0.0))
            current_x = self._approach(float(state.get("current_x", 0.0)), desired_x, rate, dt)
            current_y = self._approach(float(state.get("current_y", 0.0)), desired_y, rate, dt)
            state["current_x"], state["current_y"] = current_x, current_y
            velocity_x, velocity_y = current_x, current_y
            if str(state.get("space", "global")).lower() == "local":
                radians = math.radians(float(getattr(target, "rotation", 0.0)))
                velocity_x, velocity_y = (
                    current_x * math.cos(radians) - current_y * math.sin(radians),
                    current_x * math.sin(radians) + current_y * math.cos(radians),
                )
            if velocity_x or velocity_y:
                self._move_target(target, velocity_x, velocity_y, dt)
            self._sync_motion_debug(key, state)
            if stopping and abs(current_x) < 1e-6 and abs(current_y) < 1e-6:
                self._persistent_motion.pop(key, None)
                self._remove_motion_debug(target, key)

    @staticmethod
    def _approach(current: float, desired: float, rate: float, dt: float) -> float:
        if rate <= 0.0:
            return desired
        delta = desired - current
        step = max(0.0, rate) * max(0.0, dt)
        if abs(delta) <= step:
            return desired
        return current + math.copysign(step, delta)

    @staticmethod
    def _sync_motion_debug(handle: str, state: Mapping[str, Any]) -> None:
        target = state.get("target")
        update = getattr(target, "update_motion_debug", None)
        if callable(update):
            update(handle, {
                "name": str(state.get("name", "Movement")),
                "x": float(state.get("current_x", 0.0)),
                "y": float(state.get("current_y", 0.0)),
                "target_x": float(state.get("desired_x", 0.0)),
                "target_y": float(state.get("desired_y", 0.0)),
                "space": str(state.get("space", "global")),
                "paused": bool(state.get("paused", False)),
                "stopping": bool(state.get("stopping", False)),
                "graph": str(state.get("graph", "")),
            })

    @staticmethod
    def _remove_motion_debug(target: Any, handle: str) -> None:
        remove = getattr(target, "remove_motion_debug", None)
        if callable(remove):
            remove(handle)

    def _motions_for(self, target: Any, movement: Any = "") -> list[tuple[str, dict[str, Any]]]:
        requested = str(movement or "").strip()
        identity = self._target_identity(target)
        result: list[tuple[str, dict[str, Any]]] = []
        for handle, state in self._persistent_motion.items():
            if self._target_identity(state.get("target")) != identity:
                continue
            if requested and requested not in {handle, str(state.get("name", ""))}:
                continue
            result.append((handle, state))
        return result

    @staticmethod
    def _target_identity(target: Any) -> str:
        raw = getattr(target, "obj", None)
        if isinstance(raw, Mapping):
            return str(raw.get("id", raw.get("name", id(raw))))
        return str(getattr(target, "name", id(target)))
