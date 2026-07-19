"""Scheduler determinístico para lifecycle de componentes do Runtime."""
from __future__ import annotations

from enum import Enum
from typing import Any, Iterable


class LifecyclePhase(str, Enum):
    START = "start"
    FIXED_UPDATE = "fixed_update"
    UPDATE = "update"
    LATE_UPDATE = "late_update"
    STOP = "stop"


_HOOKS = {
    LifecyclePhase.START: "on_runtime_start",
    LifecyclePhase.FIXED_UPDATE: "on_runtime_fixed_update",
    LifecyclePhase.UPDATE: "on_runtime_update",
    LifecyclePhase.LATE_UPDATE: "on_runtime_late_update",
    LifecyclePhase.STOP: "on_runtime_stop",
}


class RuntimeLifecycleScheduler:
    """Mantém ordem de registro e aplica mutações fora da iteração."""

    def __init__(self) -> None:
        self._components: list[Any] = []
        self._component_ids: set[int] = set()
        self._pending_add: list[Any] = []
        self._pending_remove: set[int] = set()
        self.running = False

    @property
    def components(self) -> tuple[Any, ...]:
        return tuple(self._components)

    def start(self, components: Iterable[Any]) -> None:
        if self.running:
            return
        self._components.clear()
        self._component_ids.clear()
        for component in components:
            self._add_now(component)
        self.running = True
        self._dispatch(LifecyclePhase.START)

    def register(self, component: Any) -> None:
        if id(component) in self._component_ids or any(item is component for item in self._pending_add):
            return
        if self.running:
            self._pending_add.append(component)
        else:
            self._add_now(component)

    def unregister(self, component: Any) -> None:
        self._pending_remove.add(id(component))

    def fixed_update(self, delta_time: float) -> None:
        self._dispatch(LifecyclePhase.FIXED_UPDATE, float(delta_time))

    def update(self, delta_time: float) -> None:
        self._dispatch(LifecyclePhase.UPDATE, float(delta_time))

    def late_update(self, delta_time: float) -> None:
        self._dispatch(LifecyclePhase.LATE_UPDATE, float(delta_time))

    def stop(self) -> None:
        if not self.running:
            self.clear()
            return
        self._dispatch(LifecyclePhase.STOP, reverse=True)
        self.clear()

    def clear(self) -> None:
        self._components.clear()
        self._component_ids.clear()
        self._pending_add.clear()
        self._pending_remove.clear()
        self.running = False

    def _dispatch(self, phase: LifecyclePhase, *args: Any, reverse: bool = False) -> None:
        if not self.running:
            return
        hook_name = _HOOKS[phase]
        ordered = reversed(self._components) if reverse else iter(self._components)
        for component in tuple(ordered):
            if id(component) in self._pending_remove:
                continue
            if phase not in {LifecyclePhase.START, LifecyclePhase.STOP}:
                owner = getattr(component, "game_object", None)
                if not bool(getattr(component, "enabled", True)) or (owner is not None and not bool(getattr(owner, "active", True))):
                    continue
            hook = getattr(component, hook_name, None)
            if callable(hook):
                hook(*args)
        self._flush_mutations()

    def _flush_mutations(self) -> None:
        if self._pending_remove:
            self._components = [item for item in self._components if id(item) not in self._pending_remove]
            self._component_ids.difference_update(self._pending_remove)
            self._pending_remove.clear()
        pending, self._pending_add = self._pending_add, []
        for component in pending:
            self._add_now(component)
            hook = getattr(component, _HOOKS[LifecyclePhase.START], None)
            if self.running and callable(hook):
                hook()

    def _add_now(self, component: Any) -> None:
        identity = id(component)
        if identity not in self._component_ids:
            self._component_ids.add(identity)
            self._components.append(component)
