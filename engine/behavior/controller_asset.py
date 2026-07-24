"""Asset e runtime puro do Behavior Controller da Zennity.

O módulo não depende de Pygame nem de Qt. Ele pode ser usado pelo editor,
Play Mode, exportador e testes sem inicializar uma janela gráfica.
"""

from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


BEHAVIOR_CONTROLLER_FORMAT = "zennity.behavior_controller"
BEHAVIOR_CONTROLLER_VERSION = 1
PARAMETER_TYPES = {"bool", "float", "trigger"}
OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "trigger"}


def default_behavior_controller(name: str = "NewBehavior") -> dict[str, Any]:
    return {
        "format": BEHAVIOR_CONTROLLER_FORMAT,
        "version": BEHAVIOR_CONTROLLER_VERSION,
        "name": str(name).strip() or "NewBehavior",
        "initial_state": "Idle",
        "parameters": {},
        "states": {"Idle": {"script": "", "position": [40.0, 40.0]}},
        "transitions": [],
    }


def normalize_behavior_controller(data: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(data or {})
    result = default_behavior_controller(str(source.get("name", "NewBehavior")))

    states: dict[str, dict[str, Any]] = {}
    raw_states = source.get("states", {})
    if isinstance(raw_states, Mapping):
        for index, (raw_name, raw_state) in enumerate(raw_states.items()):
            name = str(raw_name).strip()
            if not name or not isinstance(raw_state, Mapping):
                continue
            fallback = [40.0 + (index % 3) * 190.0, 40.0 + (index // 3) * 120.0]
            position = raw_state.get("position", fallback)
            if not isinstance(position, (list, tuple)) or len(position) < 2:
                position = fallback
            states[name] = {
                "script": str(raw_state.get("script", "")).replace("\\", "/"),
                "enabled": bool(raw_state.get("enabled", True)),
                "position": [_safe_float(position[0], fallback[0]), _safe_float(position[1], fallback[1])],
            }
    result["states"] = states or {"Idle": {"script": "", "enabled": True, "position": [40.0, 40.0]}}

    initial = str(source.get("initial_state", "")).strip()
    result["initial_state"] = initial if initial in result["states"] else next(iter(result["states"]))

    parameters: dict[str, dict[str, Any]] = {}
    raw_parameters = source.get("parameters", {})
    if isinstance(raw_parameters, Mapping):
        for raw_name, raw_parameter in raw_parameters.items():
            name = str(raw_name).strip()
            if not name or not isinstance(raw_parameter, Mapping):
                continue
            kind = str(raw_parameter.get("type", "bool")).lower()
            if kind not in PARAMETER_TYPES:
                kind = "bool"
            if kind == "float":
                default: Any = _safe_float(raw_parameter.get("default"), 0.0)
            elif kind == "bool":
                default = bool(raw_parameter.get("default", False))
            else:
                default = False
            parameters[name] = {"type": kind, "default": default}
    result["parameters"] = parameters

    transitions: list[dict[str, Any]] = []
    raw_transitions = source.get("transitions", [])
    if isinstance(raw_transitions, list):
        for raw_transition in raw_transitions:
            if not isinstance(raw_transition, Mapping):
                continue
            origin = str(raw_transition.get("from", "*")).strip() or "*"
            target = str(raw_transition.get("to", "")).strip()
            if origin != "*" and origin not in result["states"]:
                continue
            if target not in result["states"]:
                continue
            conditions: list[dict[str, Any]] = []
            raw_conditions = raw_transition.get("conditions", [])
            if isinstance(raw_conditions, list):
                for raw_condition in raw_conditions:
                    if not isinstance(raw_condition, Mapping):
                        continue
                    parameter = str(raw_condition.get("parameter", "")).strip()
                    if parameter not in parameters:
                        continue
                    kind = parameters[parameter]["type"]
                    operator = str(raw_condition.get("operator", "trigger" if kind == "trigger" else "=="))
                    if operator not in OPERATORS:
                        operator = "=="
                    value: Any = raw_condition.get("value", True)
                    if kind == "float":
                        value = _safe_float(value, 0.0)
                    elif kind in {"bool", "trigger"}:
                        value = bool(value)
                    conditions.append({"parameter": parameter, "operator": operator, "value": value})
            transitions.append({
                "from": origin,
                "to": target,
                "conditions": conditions,
                "priority": _safe_int(raw_transition.get("priority"), 0),
            })
    result["transitions"] = transitions
    return result


def validate_behavior_controller(
    data: Mapping[str, Any] | None, project_root: str | Path | None = None
) -> list[dict[str, str]]:
    controller = normalize_behavior_controller(data)
    root = Path(project_root).resolve() if project_root is not None else None
    issues: list[dict[str, str]] = []
    for name, state in controller["states"].items():
        script = str(state.get("script", ""))
        if not script:
            issues.append({"level": "warning", "state": name, "message": f"{name}: nenhum script escolhido"})
        elif root is not None:
            path = Path(script)
            path = path if path.is_absolute() else root / path
            if not path.is_file():
                issues.append({"level": "error", "state": name, "message": f"{name}: script não encontrado"})
    seen: set[tuple[str, str, str]] = set()
    for transition in controller["transitions"]:
        key = (transition["from"], transition["to"], repr(transition.get("conditions", [])))
        if key in seen:
            issues.append({
                "level": "warning",
                "state": transition["to"],
                "message": f"Transição duplicada: {transition['from']} → {transition['to']}",
            })
        seen.add(key)
        if transition["from"] == transition["to"] and not transition.get("conditions"):
            issues.append({
                "level": "warning",
                "state": transition["to"],
                "message": f"Loop imediato sem condição em {transition['to']}",
            })
    return issues


def load_behavior_controller(path: str | Path) -> dict[str, Any]:
    controller_path = Path(path)
    with controller_path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise ValueError("O Behavior Controller deve conter um objeto JSON.")
    if raw.get("format", BEHAVIOR_CONTROLLER_FORMAT) != BEHAVIOR_CONTROLLER_FORMAT:
        raise ValueError("Formato de Behavior Controller não reconhecido.")
    return normalize_behavior_controller(raw)


def save_behavior_controller(path: str | Path, data: Mapping[str, Any]) -> dict[str, Any]:
    controller_path = Path(path)
    if controller_path.suffix.lower() != ".zbehavior":
        controller_path = controller_path.with_suffix(".zbehavior")
    controller_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_behavior_controller(data)
    temporary = controller_path.with_suffix(controller_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(normalized, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(controller_path)
    return normalized


class BehaviorControllerRuntime:
    """Máquina de estados pura que avalia parâmetros e transições."""

    def __init__(self, controller: Mapping[str, Any], parameter_values: Mapping[str, Any] | None = None) -> None:
        self.controller = normalize_behavior_controller(controller)
        self.current_state = str(self.controller["initial_state"])
        self.previous_state = ""
        self.parameters = {
            name: deepcopy(parameter["default"])
            for name, parameter in self.controller["parameters"].items()
        }
        for name, value in dict(parameter_values or {}).items():
            self._set(name, value)

    @property
    def state(self) -> dict[str, Any]:
        return self.controller["states"][self.current_state]

    @property
    def script(self) -> str:
        return str(self.state.get("script", ""))

    def play(self, state: str) -> bool:
        target = str(state)
        if target not in self.controller["states"] or target == self.current_state:
            return False
        self.previous_state = self.current_state
        self.current_state = target
        return True

    def set_bool(self, name: str, value: bool) -> None:
        self._set_typed(name, "bool", bool(value))

    def set_float(self, name: str, value: float) -> None:
        self._set_typed(name, "float", float(value))

    def trigger(self, name: str) -> None:
        self._set_typed(name, "trigger", True)

    def update(self) -> bool:
        transitions = sorted(
            self.controller["transitions"],
            key=lambda item: int(item.get("priority", 0)),
            reverse=True,
        )
        for transition in transitions:
            if transition["from"] not in {"*", self.current_state}:
                continue
            if not all(self._condition_matches(condition) for condition in transition["conditions"]):
                continue
            if self.play(transition["to"]):
                self._consume_triggers(transition)
                return True
        return False

    def _consume_triggers(self, transition: Mapping[str, Any]) -> None:
        for condition in transition.get("conditions", []):
            name = str(condition.get("parameter", ""))
            parameter = self.controller["parameters"].get(name)
            if parameter and parameter["type"] == "trigger":
                self.parameters[name] = False

    def _set(self, name: str, value: Any) -> None:
        parameter = self.controller["parameters"].get(str(name))
        if not parameter:
            return
        kind = parameter["type"]
        self.parameters[str(name)] = float(value) if kind == "float" else bool(value)

    def _set_typed(self, name: str, kind: str, value: Any) -> None:
        parameter = self.controller["parameters"].get(str(name))
        if parameter and parameter["type"] == kind:
            self.parameters[str(name)] = value

    def _condition_matches(self, condition: Mapping[str, Any]) -> bool:
        current = self.parameters.get(str(condition["parameter"]))
        expected = condition.get("value")
        operator = str(condition.get("operator", "=="))
        if operator == "trigger":
            return bool(current)
        if operator == "==":
            return current == expected
        if operator == "!=":
            return current != expected
        try:
            if operator == ">":
                return float(current) > float(expected)
            if operator == ">=":
                return float(current) >= float(expected)
            if operator == "<":
                return float(current) < float(expected)
            if operator == "<=":
                return float(current) <= float(expected)
        except (TypeError, ValueError):
            return False
        return False


class BehaviorControllerRunner:
    """Executa os hooks do script pertencente ao estado ativo."""

    def __init__(
        self,
        controller: Mapping[str, Any],
        project_root: str | Path,
        parameter_values: Mapping[str, Any] | None = None,
    ) -> None:
        self.runtime = BehaviorControllerRuntime(controller, parameter_values)
        self.project_root = Path(project_root).resolve()
        self._modules: dict[str, ModuleType | None] = {}
        self._started = False

    @property
    def current_state(self) -> str:
        return self.runtime.current_state

    @property
    def parameters(self) -> dict[str, Any]:
        return self.runtime.parameters

    def start(self, game: Any) -> None:
        if self._started:
            return
        self._started = True
        self._call("on_enter", game)

    def update(self, game: Any, dt: float) -> bool:
        if not self._started:
            self.start(game)
        self._call("on_update", game, float(dt))
        previous = self.runtime.current_state
        if not self.runtime.update():
            return False
        self._call_for_state(previous, "on_exit", game)
        self._call("on_enter", game)
        return True

    def play(self, state: str, game: Any) -> bool:
        previous = self.runtime.current_state
        if not self.runtime.play(state):
            return False
        self._call_for_state(previous, "on_exit", game)
        self._call("on_enter", game)
        return True

    def stop(self, game: Any) -> None:
        if self._started:
            self._call("on_exit", game)
        self._started = False

    def set_bool(self, name: str, value: bool) -> None:
        self.runtime.set_bool(name, value)

    def set_float(self, name: str, value: float) -> None:
        self.runtime.set_float(name, value)

    def trigger(self, name: str) -> None:
        self.runtime.trigger(name)

    def _call(self, hook_name: str, *args: Any) -> Any:
        return self._call_for_state(self.runtime.current_state, hook_name, *args)

    def _call_for_state(self, state_name: str, hook_name: str, *args: Any) -> Any:
        module = self._module_for(state_name)
        hook = getattr(module, hook_name, None) if module is not None else None
        return hook(*args) if callable(hook) else None

    def _module_for(self, state_name: str) -> ModuleType | None:
        if state_name in self._modules:
            return self._modules[state_name]
        state = self.runtime.controller["states"].get(state_name, {})
        if not bool(state.get("enabled", True)):
            self._modules[state_name] = None
            return None
        script_value = str(state.get("script", ""))
        if not script_value:
            self._modules[state_name] = None
            return None
        path = Path(script_value)
        path = path if path.is_absolute() else self.project_root / path
        path = path.resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Script do estado {state_name} não encontrado: {script_value}")
        module_name = f"zennity_behavior_{path.stem}_{abs(hash((state_name, str(path))))}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Não foi possível carregar o script do estado {state_name}: {script_value}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._modules[state_name] = module
        return module


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
