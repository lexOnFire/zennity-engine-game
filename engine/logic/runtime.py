"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

try:
    from .graph_asset import normalize_logic_graph
except ImportError:  # Runtime autocontido exportado.
    from .logic_graph_asset import normalize_logic_graph


class LogicGraphRuntime:
    """Executa fluxo e resolve valores conectados sem depender de Qt/Pygame."""

    MAX_STEPS = 256

    def __init__(self, graph: Mapping[str, Any]) -> None:
        self.graph = normalize_logic_graph(graph)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        self.incoming: dict[tuple[str, str], dict[str, Any]] = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
            self.incoming[(str(edge["to_node"]), str(edge.get("to_port", "in")))] = edge
        self.variables = {
            name: deepcopy(value.get("default")) if isinstance(value, Mapping) else deepcopy(value)
            for name, value in self.graph.get("variables", {}).items()
        }
        self.values: dict[Any, Any] = {}
        self.executed_nodes: list[str] = []
        self.started = False

    def start(self, game: Any) -> None:
        if self.started:
            return
        self.started = True
        self.values.clear()
        self.executed_nodes.clear()
        self._run_event("event_start", game, 0.0)

    def update(self, game: Any, dt: float) -> None:
        if not self.started:
            self.start(game)
        self.values.clear()
        self.executed_nodes.clear()
        self._run_event("event_update", game, float(dt))

    def _run_event(self, event_type: str, game: Any, dt: float) -> None:
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node["type"] == event_type:
                self.executed_nodes.append(str(node["id"]))
                self._follow(str(node["id"]), "next", game, dt, budget, set())

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
            self.executed_nodes.append(target_id)
            try:
                next_ports = self._execute(target, game, dt)
            except RuntimeError:
                raise
            except Exception as exc:
                raise RuntimeError(f"Nó '{target.get('title', target_id)}': {exc}") from exc
            next_branch = set(branch)
            next_branch.add(target_id)
            for next_port in next_ports:
                self._follow(target_id, next_port, game, dt, budget, next_branch)

    def _execute(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        node_type = str(node["type"])
        properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
        node_id = str(node["id"])

        if node_type == "input_axis":
            self._evaluate_output(node_id, "value", game, dt, set())
            return ["next"]
        if node_type == "key_pressed":
            pressed = bool(self._evaluate_output(node_id, "value", game, dt, set()))
            return ["true" if pressed else "false"]
        if node_type == "is_grounded":
            grounded = bool(self._evaluate_output(node_id, "value", game, dt, set()))
            return ["true" if grounded else "false"]
        if node_type == "if_else":
            raw = self._read_input(node_id, "condition", properties.get("condition", False), game, dt, set())
            condition = self._condition(raw)
            self._store(node_id, "value", condition)
            return ["true" if condition else "false"]
        if node_type == "compare_number":
            condition = bool(self._evaluate_output(node_id, "value", game, dt, set()))
            return ["true" if condition else "false"]
        if node_type == "move":
            fallback = self.values.get("axis", 0.0)
            amount = float(self._read_input(node_id, "value", fallback, game, dt, set()))
            game.move(amount * float(properties.get("speed", 200.0)) * dt)
            return ["next"]
        if node_type == "jump":
            force = float(self._read_input(node_id, "force", properties.get("force", 420.0), game, dt, set()))
            game.jump(force)
            return ["next"]
        if node_type == "play_animation":
            state = self._read_input(node_id, "state", properties.get("state", "Idle"), game, dt, set())
            game.animator.play(str(state))
            return ["next"]
        if node_type == "play_sound":
            path = str(self._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
            if path:
                game.play_sound(path)
            return ["next"]
        if node_type == "set_hud":
            text = self._read_input(node_id, "text", properties.get("text", "Texto"), game, dt, set())
            game.set_hud(f"logic:{node_id}", str(text))
            return ["next"]
        if node_type == "set_variable":
            name = str(properties.get("name", "value"))
            value = self._read_input(node_id, "value", properties.get("value"), game, dt, set())
            self.variables[name] = deepcopy(value)
            self._store(node_id, "value", value)
            return ["next"]
        if node_type == "get_variable":
            self._evaluate_output(node_id, "value", game, dt, set())
            return ["next"]
        if node_type == "sequence":
            outputs = max(1, int(properties.get("outputs", 2)))
            return [f"then_{index}" for index in range(outputs)] + ["next"]
        return ["next"]

    def _read_input(
        self,
        node_id: str,
        port: str,
        default: Any,
        game: Any,
        dt: float,
        resolving: set[tuple[str, str]],
    ) -> Any:
        edge = self.incoming.get((node_id, port))
        if edge is None:
            return deepcopy(default)
        return self._evaluate_output(
            str(edge["from_node"]), str(edge.get("from_port", "value")), game, dt, resolving
        )

    def _evaluate_output(
        self,
        node_id: str,
        port: str,
        game: Any,
        dt: float,
        resolving: set[tuple[str, str]],
    ) -> Any:
        key = (node_id, port)
        if key in self.values:
            return self.values[key]
        if key in resolving:
            node = self.nodes.get(node_id, {})
            raise RuntimeError(f"Ciclo de dados detectado no nó '{node.get('title', node_id)}'.")
        node = self.nodes.get(node_id)
        if node is None:
            raise RuntimeError(f"Origem de dados não encontrada: {node_id}")
        if node_id not in self.executed_nodes:
            self.executed_nodes.append(node_id)
        resolving = set(resolving)
        resolving.add(key)
        properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
        node_type = str(node.get("type", ""))

        if node_type == "input_axis":
            negative = str(properties.get("negative", "A")).lower()
            positive = str(properties.get("positive", "D")).lower()
            value = float(game.axis(negative, positive))
            self.values["axis"] = value
        elif node_type == "key_pressed":
            value = bool(game.key_pressed(str(properties.get("key", "space")).lower()))
        elif node_type == "is_grounded":
            value = bool(game.grounded)
        elif node_type == "compare_number":
            left = self._read_input(node_id, "value", self.values.get("axis", 0.0), game, dt, resolving)
            value = self._compare(left, properties.get("operator", ">"), properties.get("value", 0.0))
        elif node_type == "and":
            left = bool(self._read_input(node_id, "a", False, game, dt, resolving))
            right = bool(self._read_input(node_id, "b", False, game, dt, resolving))
            value = left and right
        elif node_type == "or":
            left = bool(self._read_input(node_id, "a", False, game, dt, resolving))
            right = bool(self._read_input(node_id, "b", False, game, dt, resolving))
            value = left or right
        elif node_type == "get_variable":
            value = deepcopy(self.variables.get(str(properties.get("name", "value"))))
        elif node_type in {"number_value", "bool_value", "text_value"}:
            value = deepcopy(properties.get("value"))
        elif node_type == "self_object":
            value = game
        elif node_type == "find_tag":
            value = game.find(str(properties.get("tag", "Player")))
        elif node_type == "if_else":
            raw = self._read_input(node_id, "condition", properties.get("condition", False), game, dt, resolving)
            value = self._condition(raw)
        else:
            value = self.values.get(node_id, properties.get(port))
        return self._store(node_id, port, value)

    def _store(self, node_id: str, port: str, value: Any) -> Any:
        self.values[(node_id, port)] = value
        self.values[node_id] = value  # Compatibilidade com extensões antigas.
        return value

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
