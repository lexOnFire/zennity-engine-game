"""Assets e runtime leve do Animator Controller da Zennity."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping


ANIMATOR_CONTROLLER_FORMAT = "zennity.animator_controller"
ANIMATOR_CONTROLLER_VERSION = 1
PARAMETER_TYPES = {"bool", "float", "trigger"}
OPERATORS = {"==", "!=", ">", ">=", "<", "<=", "trigger"}


def default_animator_controller(name: str = "NewController") -> dict[str, Any]:
    return {
        "format": ANIMATOR_CONTROLLER_FORMAT,
        "version": ANIMATOR_CONTROLLER_VERSION,
        "name": str(name).strip() or "NewController",
        "initial_state": "Idle",
        "parameters": {},
        "states": {"Idle": {"animation": "", "speed": 1.0, "position": [40.0, 40.0]}},
        "transitions": [],
    }


def normalize_animator_controller(data: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(data or {})
    result = default_animator_controller(str(source.get("name", "NewController")))

    states: dict[str, dict[str, Any]] = {}
    raw_states = source.get("states", {})
    if isinstance(raw_states, Mapping):
        for index, (raw_name, raw_state) in enumerate(raw_states.items()):
            name = str(raw_name).strip()
            if not name or not isinstance(raw_state, Mapping):
                continue
            raw_position = raw_state.get("position", [40.0 + (index % 3) * 190.0, 40.0 + (index // 3) * 120.0])
            if not isinstance(raw_position, (list, tuple)) or len(raw_position) < 2:
                raw_position = [40.0 + (index % 3) * 190.0, 40.0 + (index // 3) * 120.0]
            states[name] = {
                "animation": str(raw_state.get("animation", "")).replace("\\", "/"),
                "speed": max(0.0, _safe_float(raw_state.get("speed"), 1.0)),
                "position": [_safe_float(raw_position[0], 40.0), _safe_float(raw_position[1], 40.0)],
            }
    result["states"] = states or {"Idle": {"animation": "", "speed": 1.0, "position": [40.0, 40.0]}}
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
            default: Any = False if kind in {"bool", "trigger"} else 0.0
            if kind == "float":
                default = _safe_float(raw_parameter.get("default"), 0.0)
            elif kind == "bool":
                default = bool(raw_parameter.get("default", False))
            parameters[name] = {"type": kind, "default": default}
    result["parameters"] = parameters

    transitions: list[dict[str, Any]] = []
    raw_transitions = source.get("transitions", [])
    if isinstance(raw_transitions, list):
        for raw_transition in raw_transitions:
            if not isinstance(raw_transition, Mapping):
                continue
            origin = str(raw_transition.get("from", "")).strip()
            target = str(raw_transition.get("to", "")).strip()
            if origin != "*" and origin not in result["states"]:
                continue
            if target not in result["states"]:
                continue
            conditions: list[dict[str, Any]] = []
            for raw_condition in raw_transition.get("conditions", []):
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
            transitions.append({"from": origin or "*", "to": target, "conditions": conditions})
    result["transitions"] = transitions
    return result


def validate_animator_controller(
    data: Mapping[str, Any] | None, project_root: str | Path | None = None
) -> list[dict[str, str]]:
    """Retorna problemas amigáveis para o editor, sem impedir assets incompletos."""
    controller = normalize_animator_controller(data)
    root = Path(project_root).resolve() if project_root is not None else None
    issues: list[dict[str, str]] = []
    for name, state in controller["states"].items():
        animation = str(state.get("animation", ""))
        if not animation:
            issues.append({"level": "warning", "state": name, "message": f"{name}: nenhuma animação escolhida"})
        elif root is not None:
            path = Path(animation)
            path = path if path.is_absolute() else root / path
            if not path.is_file():
                issues.append({"level": "error", "state": name, "message": f"{name}: animação não encontrada"})
    seen: set[tuple[str, str, str]] = set()
    for transition in controller["transitions"]:
        condition_key = repr(transition.get("conditions", []))
        key = (transition["from"], transition["to"], condition_key)
        if key in seen:
            issues.append({"level": "warning", "state": transition["to"], "message": f"Transição duplicada: {transition['from']} → {transition['to']}"})
        seen.add(key)
        if transition["from"] == transition["to"] and not transition.get("conditions"):
            issues.append({"level": "warning", "state": transition["to"], "message": f"Loop imediato sem condição em {transition['to']}"})
    return issues


def load_animator_controller(path: str | Path) -> dict[str, Any]:
    controller_path = Path(path)
    with controller_path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise ValueError("O Animator Controller deve conter um objeto JSON.")
    if raw.get("format", ANIMATOR_CONTROLLER_FORMAT) != ANIMATOR_CONTROLLER_FORMAT:
        raise ValueError("Formato de Animator Controller não reconhecido.")
    return normalize_animator_controller(raw)


def save_animator_controller(path: str | Path, data: Mapping[str, Any]) -> dict[str, Any]:
    controller_path = Path(path)
    if controller_path.suffix.lower() != ".zanimator":
        controller_path = controller_path.with_suffix(".zanimator")
    controller_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_animator_controller(data)
    temporary = controller_path.with_suffix(controller_path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(normalized, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temporary.replace(controller_path)
    return normalized


class AnimatorControllerRuntime:
    """Máquina de estados pura, sem dependência de Pygame ou Qt."""

    def __init__(self, controller: Mapping[str, Any], parameter_values: Mapping[str, Any] | None = None) -> None:
        self.controller = normalize_animator_controller(controller)
        self.current_state = str(self.controller["initial_state"])
        self.parameters = {
            name: deepcopy(parameter["default"])
            for name, parameter in self.controller["parameters"].items()
        }
        for name, value in dict(parameter_values or {}).items():
            self._set(name, value)

    def play(self, state: str) -> bool:
        state = str(state)
        if state not in self.controller["states"]:
            return False
        changed = state != self.current_state
        self.current_state = state
        return changed

    def set_bool(self, name: str, value: bool) -> None:
        self._set_typed(name, "bool", bool(value))

    def set_float(self, name: str, value: float) -> None:
        self._set_typed(name, "float", float(value))

    def trigger(self, name: str) -> None:
        self._set_typed(name, "trigger", True)

    def update(self) -> bool:
        changed = False
        for transition in self.controller["transitions"]:
            if transition["from"] not in {"*", self.current_state}:
                continue
            if all(self._condition_matches(condition) for condition in transition["conditions"]):
                changed = self.play(transition["to"])
                break
        for name, parameter in self.controller["parameters"].items():
            if parameter["type"] == "trigger":
                self.parameters[name] = False
        return changed

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
        name = str(condition["parameter"])
        current = self.parameters.get(name)
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


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
