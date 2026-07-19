from __future__ import annotations

import hashlib
import importlib.util
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from engine.components.script_component import ScriptComponent
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

    def __init__(self, runtime_scene: Any, project_root: str | Path | None = None) -> None:
        self.runtime_scene = runtime_scene
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.instances: dict[ScriptComponent, ScriptRuntimeInstance] = {}
        self.errors: list[str] = []

    def start(self, components: list[Any]) -> None:
        for component in components:
            if isinstance(component, ScriptComponent):
                self._start_component(component)

    def update(self, delta_time: float) -> None:
        self._update_phase("on_update", delta_time)

    def fixed_update(self, delta_time: float) -> None:
        self._update_phase("on_fixed_update", delta_time)

    def late_update(self, delta_time: float) -> None:
        self._update_phase("on_late_update", delta_time)

    def _update_phase(self, method_name: str, delta_time: float) -> None:
        for instance in list(self.instances.values()):
            component = instance.component
            if not bool(getattr(component, "enabled", True)):
                continue
            try:
                getattr(instance.behaviour, method_name)(float(delta_time))
            except Exception as exc:
                self._handle_error(component, method_name, exc)

    def stop(self) -> None:
        for instance in list(reversed(list(self.instances.values()))):
            try:
                instance.behaviour.on_destroy()
            except Exception as exc:
                self._record_error(instance.component, "on_destroy", exc)
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
            instance = ScriptRuntimeInstance(component, behaviour, module, path)
            self.instances[component] = instance
            behaviour.on_awake()
            behaviour.on_start()
            instance.started = True
        except Exception as exc:
            self._handle_error(component, "start", exc)

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
        spec.loader.exec_module(module)
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
        if phase == "start":
            self.instances.pop(component, None)
        self._record_error(component, phase, exc)

    def _record_error(self, component: ScriptComponent, phase: str, exc: Exception) -> None:
        obj_name = getattr(getattr(component, "game_object", None), "name", "<detached>")
        message = f"{obj_name}:{getattr(component, 'script_path', '')}:{phase}: {exc}"
        self.errors.append(message)
        print(f"[ScriptRuntime] {message}")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
