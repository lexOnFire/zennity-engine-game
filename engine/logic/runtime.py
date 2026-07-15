"""Executor leve dos grafos visuais ``.zlogic``."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

try:
    from .graph_asset import normalize_logic_graph
except ImportError:  # Runtime autocontido exportado.
    from .logic_graph_asset import normalize_logic_graph


class LogicGraphRuntime:
    """Interpreta nós de fluxo sem depender de Qt ou Pygame."""

    MAX_STEPS = 256

    def __init__(self, graph: Mapping[str, Any]) -> None:
        self.graph = normalize_logic_graph(graph)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
        self.variables = {
            name: deepcopy(value.get("default")) if isinstance(value, Mapping) else deepcopy(value)
            for name, value in self.graph.get("variables", {}).items()
        }
        self.values: dict[str, Any] = {}
        self.started = False

    def start(self, game: Any) -> None:
        if self.started:
            return
        self.started = True
        self._run_event("event_start", game, 0.0)

    def update(self, game: Any, dt: float) -> None:
        if not self.started:
            self.start(game)
        self.values.clear()
        self._run_event("event_update", game, float(dt))

    def _run_event(self, event_type: str, game: Any, dt: float) -> None:
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node["type"] == event_type:
                self._follow(node["id"], "next", game, dt, budget, set())

    def _follow(
        self,
        node_id: str,
        port: str,
        game: Any,
        dt: float,
        budget: list[int],
        branch: set[str],
    ) -> None:
        if budget[0] <= 0:
            raise RuntimeError("Logic Graph excedeu o limite de execução; verifique loops no grafo.")
        for edge in self.outgoing.get(node_id, []):
            if str(edge.get("from_port", "next")) != port:
                continue
            target_id = str(edge["to_node"])
            if target_id in branch:
                raise RuntimeError("Logic Graph contém um loop de execução sem espera.")
            target = self.nodes.get(target_id)
            if target is None:
                continue
            budget[0] -= 1
            next_ports = self._execute(target, game, dt)
            next_branch = set(branch)
            next_branch.add(target_id)
            for next_port in next_ports:
                self._follow(target_id, next_port, game, dt, budget, next_branch)

    def _execute(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        node_type = str(node["type"])
        properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
        node_id = str(node["id"])

        if node_type == "input_axis":
            negative = str(properties.get("negative", "A")).lower()
            positive = str(properties.get("positive", "D")).lower()
            axis = float(game.axis(negative, positive))
            self.values[node_id] = axis
            self.values["axis"] = axis
            return ["next"]
        if node_type == "key_pressed":
            pressed = bool(game.key_pressed(str(properties.get("key", "space")).lower()))
            self.values[node_id] = pressed
            return ["true" if pressed else "false"]
        if node_type == "is_grounded":
            grounded = bool(game.grounded)
            self.values[node_id] = grounded
            return ["true" if grounded else "false"]
        if node_type == "if_else":
            condition = self._condition(properties.get("condition", False))
            self.values[node_id] = condition
            return ["true" if condition else "false"]
        if node_type == "compare_number":
            condition = self._compare(self.values.get("axis", 0.0), properties.get("operator", ">"), properties.get("value", 0.0))
            self.values[node_id] = condition
            return ["true" if condition else "false"]
        if node_type == "move":
            axis = float(self.values.get("axis", 0.0))
            game.move(axis * float(properties.get("speed", 200.0)) * dt)
            return ["next"]
        if node_type == "jump":
            game.jump(float(properties.get("force", 420.0)))
            return ["next"]
        if node_type == "play_animation":
            game.animator.play(str(properties.get("state", "Idle")))
            return ["next"]
        if node_type == "play_sound":
            path = str(properties.get("path", ""))
            if path:
                game.play_sound(path)
            return ["next"]
        if node_type == "set_hud":
            game.set_hud(f"logic:{node_id}", str(properties.get("text", "Texto")))
            return ["next"]
        if node_type == "set_variable":
            self.variables[str(properties.get("name", "value"))] = deepcopy(properties.get("value"))
            return ["next"]
        if node_type == "get_variable":
            self.values[node_id] = deepcopy(self.variables.get(str(properties.get("name", "value"))))
            return ["next"]
        if node_type == "sequence":
            outputs = max(1, int(properties.get("outputs", 2)))
            return [f"then_{index}" for index in range(outputs)] + ["next"]
        return ["next"]

    def _condition(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        text = str(value).strip().replace(" ", "").lower()
        axis = float(self.values.get("axis", 0.0))
        if text in {"axis!=0", "movimento!=0"}:
            return axis != 0.0
        if text in {"axis==0", "movimento==0"}:
            return axis == 0.0
        if text in {"true", "verdadeiro", "1"}:
            return True
        if text in {"false", "falso", "0", ""}:
            return False
        return bool(self.variables.get(str(value), False))

    @staticmethod
    def _compare(left: Any, operator: Any, right: Any) -> bool:
        try:
            left_number, right_number = float(left), float(right)
        except (TypeError, ValueError):
            return False
        return {
            "==": left_number == right_number,
            "!=": left_number != right_number,
            ">": left_number > right_number,
            ">=": left_number >= right_number,
            "<": left_number < right_number,
            "<=": left_number <= right_number,
        }.get(str(operator), False)
