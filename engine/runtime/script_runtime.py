from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from engine.components.script_component import ScriptComponent
from engine.diagnostics import get_logger, report_error
from engine.runtime.lifecycle_scheduler import LifecycleEntry, LifecycleScheduler

_log = get_logger("runtime")
from engine.runtime.script_behaviour import ScriptBehaviour


@dataclass
class ScriptRuntimeInstance:
    component: ScriptComponent
    behaviour: ScriptBehaviour
    module: ModuleType
    path: Path
    started: bool = False


class ScriptRuntime:
    """Loads and executes ScriptComponent Python behaviours in Runtime World."""

    def __init__(
        self,
        runtime_scene: Any,
        project_root: str | Path | None = None,
        scheduler: LifecycleScheduler | None = None,
    ) -> None:
        self.runtime_scene = runtime_scene
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.instances: dict[ScriptComponent, ScriptRuntimeInstance] = {}
        self.errors: list[str] = []
        self.scheduler = scheduler or LifecycleScheduler()
        self._owns_scheduler = scheduler is None
        self._physics_event_handlers: list[Any] = []

    def start(self, components: list[Any]) -> None:
        for component in components:
            if isinstance(component, ScriptComponent):
                self._start_component(component)
        if self._owns_scheduler:
            self.scheduler.start()

    def update(self, delta_time: float) -> None:
        if self._owns_scheduler:
            self.scheduler.update(float(delta_time))

    def fixed_update(self, delta_time: float) -> None:
        if self._owns_scheduler:
            self.scheduler.run_fixed_updates(float(delta_time))

    def late_update(self, delta_time: float) -> None:
        if self._owns_scheduler:
            self.scheduler.late_update(float(delta_time))

    def stop(self) -> None:
        if self._owns_scheduler:
            self.scheduler.stop()
        else:
            for component in list(self.instances):
                self.scheduler.unregister(self._scheduler_key(component))
        self.instances.clear()

    def notify_game_object_event(self, game_object: Any, method_name: str, other: Any) -> None:
        for instance in list(self.instances.values()):
            if instance.behaviour.game_object is not game_object:
                continue
            method = getattr(instance.behaviour, method_name, None)
            if method is None:
                continue
            try:
                method(other)
            except Exception as exc:
                self._handle_error(instance.component, method_name, exc)

        # Phase 5B.2: Dispatch to Logic Graph runtimes
        if method_name in ("on_collision_enter", "on_collision_exit", "on_trigger_enter", "on_trigger_exit"):
            try:
                from engine.logic.physics_event_dispatch import dispatch_physics_event
                dispatch_physics_event(game_object, method_name, other)
            except Exception as exc:
                self._record_error(None, f"physics_event_dispatch[{method_name}]", exc)

    def _start_component(self, component: ScriptComponent) -> None:
        script_path = str(getattr(component, "script_path", "") or "").strip()
        if not script_path:
            return
        try:
            path = self._resolve_path(script_path)
            module = self._load_module(path)
            behaviour_type = self._find_behaviour_type(module)
            behaviour = behaviour_type()
            behaviour.game_object = component.game_object
            behaviour.runtime = self
            behaviour.scene = self.runtime_scene
            instance = ScriptRuntimeInstance(component, behaviour, module, path)
            self.instances[component] = instance
            self.scheduler.register(
                LifecycleEntry(
                    key=self._scheduler_key(component),
                    enabled=lambda component=component: bool(getattr(component, "enabled", True)),
                    awake=lambda: self._call(instance, "on_awake"),
                    start=lambda: self._mark_started(instance),
                    update=lambda dt: self._call(instance, "on_update", dt),
                    fixed_update=lambda dt: self._call(instance, "on_fixed_update", dt),
                    late_update=lambda dt: self._call(instance, "on_late_update", dt),
                    stop=lambda: self._call(instance, "on_destroy", disable_on_error=False),
                )
            )
        except Exception as exc:
            self._handle_error(component, "start", exc)

    def _scheduler_key(self, component: ScriptComponent) -> tuple[str, int]:
        return ("script", id(component))

    def _mark_started(self, instance: ScriptRuntimeInstance) -> None:
        self._call(instance, "on_start")
        instance.started = True

    def _call(
        self,
        instance: ScriptRuntimeInstance,
        method_name: str,
        *args: Any,
        disable_on_error: bool = True,
    ) -> None:
        try:
            getattr(instance.behaviour, method_name)(*args)
        except Exception as exc:
            if disable_on_error:
                self._handle_error(instance.component, method_name, exc)
            else:
                self._record_error(instance.component, method_name, exc)

    def _resolve_path(self, script_path: str) -> Path:
        path = Path(script_path)
        if not path.is_absolute():
            path = self.project_root / path
        path = path.resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Script not found: {script_path}")
        return path

    def _load_module(self, path: Path) -> ModuleType:
        digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:12]
        module_name = f"zennity_runtime_script_{path.stem}_{digest}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load script module: {path}")
        module = importlib.util.module_from_spec(spec)
        # Compile the current bytes directly.  SourceFileLoader may reuse a
        # timestamp-based .pyc when several hot reloads happen in one second.
        source = path.read_bytes()
        code = compile(source, str(path), "exec")
        exec(code, module.__dict__)
        return module

    def _find_behaviour_type(self, module: ModuleType) -> type[ScriptBehaviour]:
        explicit = getattr(module, "Script", None)
        if isinstance(explicit, type) and issubclass(explicit, ScriptBehaviour) and explicit is not ScriptBehaviour:
            return explicit
        for value in module.__dict__.values():
            if isinstance(value, type) and issubclass(value, ScriptBehaviour) and value is not ScriptBehaviour:
                return value
        raise TypeError("Script module must define a ScriptBehaviour subclass")

    def _handle_error(self, component: ScriptComponent, phase: str, exc: Exception) -> None:
        component.enabled = False
        if phase in {"start", "on_awake", "on_start"}:
            self.instances.pop(component, None)
            self.scheduler.unregister(self._scheduler_key(component))
        self._record_error(component, phase, exc)

    def _record_error(self, component: ScriptComponent, phase: str, exc: Exception) -> None:
        obj_name = getattr(getattr(component, "game_object", None), "name", "<detached>")
        message = f"{obj_name}:{getattr(component, 'script_path', '')}:{phase}: {exc}"
        self.errors.append(message)
        # Single funnel for every script failure: previously print()-only, which
        # is invisible from the viewport subprocess (Phase 9.5B Stage 0).
        report_error(_log, f"run script phase {phase!r} on {obj_name}", exc)
