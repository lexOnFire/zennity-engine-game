from __future__ import annotations

import hashlib
import importlib.util
import traceback
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from engine.components.script_component import ScriptComponent
from engine.runtime.lifecycle_scheduler import LifecycleEntry, LifecycleScheduler
from engine.runtime.script_behaviour import ScriptBehaviour


@dataclass
class ScriptRuntimeInstance:
    component: ScriptComponent
    behaviour: ScriptBehaviour
    module: ModuleType
    path: Path
    started: bool = False
    source_signature: tuple[int, int] = (0, 0)
    source_fingerprint: str = ""
    failed_fingerprint: str = ""


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

    def start(self, components: list[Any]) -> None:
        for component in components:
            if isinstance(component, ScriptComponent):
                self._start_component(component)
        if self._owns_scheduler:
            self.scheduler.start()

    def update(self, delta_time: float) -> None:
        self.reload_changed()
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
            signature, fingerprint = self._source_identity(path)
            instance = ScriptRuntimeInstance(
                component,
                behaviour,
                module,
                path,
                source_signature=signature,
                source_fingerprint=fingerprint,
            )
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

    def reload_changed(self) -> list[Path]:
        """Transactionally reload changed scripts without restarting the scene."""
        reloaded: list[Path] = []
        for instance in list(self.instances.values()):
            try:
                signature = self._source_signature(instance.path)
                if signature == instance.source_signature:
                    continue
                fingerprint = self._source_fingerprint(instance.path)
                if fingerprint == instance.source_fingerprint:
                    instance.source_signature = signature
                    continue
                if fingerprint == instance.failed_fingerprint:
                    continue
                self._reload_instance(instance, signature, fingerprint)
                reloaded.append(instance.path)
            except Exception as exc:
                try:
                    failed_fingerprint = self._source_fingerprint(instance.path)
                except OSError:
                    failed_fingerprint = "<unreadable>"
                if failed_fingerprint == instance.failed_fingerprint:
                    continue
                instance.failed_fingerprint = failed_fingerprint
                self._record_error(instance.component, "reload", exc)
        return reloaded

    def _reload_instance(
        self,
        instance: ScriptRuntimeInstance,
        signature: tuple[int, int],
        fingerprint: str,
    ) -> None:
        module = self._load_module(instance.path)
        behaviour_type = self._find_behaviour_type(module)
        state = self._capture_reload_state(instance.behaviour)
        candidate = behaviour_type()
        candidate.game_object = instance.behaviour.game_object
        candidate.runtime = self
        candidate.scene = self.runtime_scene
        for name, value in state.items():
            setattr(candidate, name, self._copy_state(value))
        candidate.on_reload(self._copy_state(state))
        instance.behaviour = candidate
        instance.module = module
        instance.source_signature = signature
        instance.source_fingerprint = fingerprint
        instance.failed_fingerprint = ""

    def _capture_reload_state(self, behaviour: ScriptBehaviour) -> dict[str, Any]:
        state = {
            name: self._copy_state(value)
            for name, value in vars(behaviour).items()
            if not name.startswith("_")
            and name not in {"game_object", "runtime", "scene", "input"}
        }
        supplied = behaviour.on_before_reload()
        if supplied is not None:
            if not isinstance(supplied, dict):
                raise TypeError("on_before_reload must return a dict or None")
            state.update(deepcopy(supplied))
        return state

    @staticmethod
    def _copy_state(value: Any) -> Any:
        try:
            return deepcopy(value)
        except (TypeError, ValueError):
            return value

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

    @staticmethod
    def _source_signature(path: Path) -> tuple[int, int]:
        stat = path.stat()
        return int(stat.st_mtime_ns), int(stat.st_size)

    @classmethod
    def _source_identity(cls, path: Path) -> tuple[tuple[int, int], str]:
        return cls._source_signature(path), cls._source_fingerprint(path)

    @staticmethod
    def _source_fingerprint(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

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
        print(f"[ScriptRuntime] {message}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
