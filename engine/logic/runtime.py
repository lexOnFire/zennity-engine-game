"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

import ast
import re
from copy import deepcopy
from typing import Any, Iterator, Mapping

try:
    from .graph_asset import normalize_logic_graph
    from .blackboard import BlackboardStore
except ImportError:  # Runtime autocontido exportado.
    from .logic_graph_asset import normalize_logic_graph
    from .logic_blackboard import BlackboardStore


class LogicGraphRuntime:
    """Executa fluxo e resolve valores conectados sem depender de Qt/Pygame."""

    MAX_STEPS = 256

    def __init__(
        self,
        graph: Mapping[str, Any],
        blackboard: BlackboardStore | None = None,
        object_key: str = "Object",
    ) -> None:
        self.graph = normalize_logic_graph(graph)
        self.object_key = str(object_key)
        self.blackboard = blackboard or BlackboardStore()
        self.blackboard.register(self.graph.get("variables", {}), self.object_key)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        self.incoming: dict[tuple[str, str], dict[str, Any]] = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
            self.incoming[(str(edge["to_node"]), str(edge.get("to_port", "in")))] = edge
        self.variables = self.blackboard.values_for_object(self.object_key)
        self.values: dict[Any, Any] = {}
        self.executed_nodes: list[str] = []
        self.executed_edges: list[str] = []
        self.breakpoints = {str(value) for value in self.graph.get("debug", {}).get("breakpoints", [])}
        self.breakpoint_conditions = {
            str(node_id): str(expression)
            for node_id, expression in self.graph.get("debug", {}).get("breakpoint_conditions", {}).items()
        }
        self.watch_expressions = [str(value) for value in self.graph.get("debug", {}).get("watches", [])]
        self.debug_paused = False
        self.pause_node = ""
        self.debug_condition_error = ""
        self._debug_generator: Iterator[str] | None = None
        self._debug_waiting_node: str | None = None
        self._debug_bypass_node = ""
        self._debug_game: Any = None
        self._debug_dt = 0.0
        self.started = False

    def start(self, game: Any) -> None:
        if self.started:
            return
        self.started = True
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        if self.breakpoints:
            self._begin_debug_event("event_start", game, 0.0)
        else:
            self._run_event("event_start", game, 0.0)

    def update(self, game: Any, dt: float) -> None:
        if not self.started:
            self.start(game)
        if self.debug_paused:
            return
        if self.breakpoints:
            if self._debug_generator is None:
                self.values.clear()
                self.executed_nodes.clear()
                self.executed_edges.clear()
                self._begin_debug_event("event_update", game, float(dt))
            else:
                self._drive_debug()
            return
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self._run_event("event_update", game, float(dt))

    def configure_breakpoints(
        self,
        node_ids: list[str] | set[str] | tuple[str, ...],
        conditions: Mapping[str, Any] | None = None,
        watches: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> None:
        self.breakpoints = {str(node_id) for node_id in node_ids if str(node_id) in self.nodes}
        if conditions is not None:
            self.breakpoint_conditions = {
                str(node_id): str(expression).strip()
                for node_id, expression in conditions.items()
                if str(node_id) in self.breakpoints and str(expression).strip()
            }
        if watches is not None:
            self.watch_expressions = list(dict.fromkeys(str(value).strip() for value in watches if str(value).strip()))
        if not self.breakpoints:
            self.debug_paused = False
            self.pause_node = ""
            self._debug_generator = None
            self._debug_waiting_node = None
            self._debug_bypass_node = ""
            self.debug_condition_error = ""

    def configure_variables(self, definitions: Mapping[str, Any]) -> None:
        """Registra alterações do painel Blackboard sem reiniciar o Play Mode."""
        self.graph["variables"] = deepcopy(dict(definitions))
        self.blackboard.register(self.graph["variables"], self.object_key)
        self.variables = self.blackboard.values_for_object(self.object_key)

    def continue_execution(self) -> None:
        if not self.debug_paused:
            return
        self._debug_bypass_node = self.pause_node
        self.debug_paused = False
        self.pause_node = ""
        self.debug_condition_error = ""

    def step(self) -> None:
        if not self.debug_paused or self._debug_generator is None:
            return
        self._debug_bypass_node = self.pause_node
        self.debug_paused = False
        self.pause_node = ""
        self._drive_debug(step_once=True)

    def restart(self, game: Any, dt: float = 0.0) -> None:
        """Reinicia variáveis e fluxo, avançando novamente até o primeiro breakpoint."""
        self.blackboard.reset_object(self.object_key)
        self.variables = self.blackboard.values_for_object(self.object_key)
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self.debug_paused = False
        self.pause_node = ""
        self.debug_condition_error = ""
        self._debug_generator = None
        self._debug_waiting_node = None
        self._debug_bypass_node = ""
        self.started = False
        self.start(game)
        if not self.debug_paused:
            self.update(game, float(dt))

    def _begin_debug_event(self, event_type: str, game: Any, dt: float) -> None:
        self._debug_game = game
        self._debug_dt = float(dt)
        self._debug_generator = self._debug_event_generator(event_type, game, dt)
        self._debug_waiting_node = None
        self._drive_debug()

    def _drive_debug(self, step_once: bool = False) -> None:
        executed = 0
        while self._debug_generator is not None:
            if self._debug_waiting_node is None:
                try:
                    self._debug_waiting_node = next(self._debug_generator)
                except StopIteration:
                    self._finish_debug_flow(step_once)
                    return
            if step_once and executed >= 1:
                self.debug_paused = True
                self.pause_node = str(self._debug_waiting_node or "")
                return
            waiting = str(self._debug_waiting_node)
            if waiting in self.breakpoints and self._debug_bypass_node != waiting:
                condition = self.breakpoint_conditions.get(waiting, "").strip()
                try:
                    should_pause = not condition or bool(self._evaluate_debug_expression(condition))
                    self.debug_condition_error = ""
                except ValueError as exc:
                    should_pause = True
                    self.debug_condition_error = f"Condição inválida em '{condition}': {exc}"
                if should_pause:
                    self.debug_paused = True
                    self.pause_node = waiting
                    return
            self._debug_waiting_node = None
            if self._debug_bypass_node == waiting:
                self._debug_bypass_node = ""
            try:
                self._debug_waiting_node = next(self._debug_generator)
                executed += 1
            except StopIteration:
                executed += 1
                self._finish_debug_flow(step_once)
                return

    def _finish_debug_flow(self, keep_paused: bool) -> None:
        self._debug_generator = None
        self._debug_waiting_node = None
        self._debug_bypass_node = ""
        self.debug_paused = bool(keep_paused)
        self.pause_node = ""

    def _debug_event_generator(self, event_type: str, game: Any, dt: float) -> Iterator[str]:
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node["type"] != event_type:
                continue
            node_id = str(node["id"])
            yield node_id
            if node_id not in self.executed_nodes:
                self.executed_nodes.append(node_id)
            yield from self._follow_debug(node_id, "next", game, dt, budget, set())

    def _follow_debug(
        self,
        node_id: str,
        port: str,
        game: Any,
        dt: float,
        budget: list[int],
        branch: set[str],
    ) -> Iterator[str]:
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
            edge_id = str(edge.get("id", ""))
            if edge_id and edge_id not in self.executed_edges:
                self.executed_edges.append(edge_id)
            yield target_id
            if target_id not in self.executed_nodes:
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
                yield from self._follow_debug(target_id, next_port, game, dt, budget, next_branch)

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
            edge_id = str(edge.get("id", ""))
            if edge_id and edge_id not in self.executed_edges:
                self.executed_edges.append(edge_id)
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
            scope = str(properties.get("scope", "object")).lower()
            value = self._read_input(node_id, "value", properties.get("value"), game, dt, set())
            value = self.blackboard.set(scope, name, value, self.object_key)
            self.variables = self.blackboard.values_for_object(self.object_key)
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
        edge_id = str(edge.get("id", ""))
        if edge_id and edge_id not in self.executed_edges:
            self.executed_edges.append(edge_id)
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
            value = self.blackboard.get(
                str(properties.get("scope", "object")).lower(),
                str(properties.get("name", "value")),
                self.object_key,
            )
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

    def debug_snapshot(self) -> dict[str, Any]:
        """Retorna somente dados pequenos e serializáveis para o editor Qt."""
        values: dict[str, dict[str, Any]] = {}
        for key, value in self.values.items():
            if not isinstance(key, tuple) or len(key) != 2:
                continue
            node_id, port = str(key[0]), str(key[1])
            values.setdefault(node_id, {})[port] = self._debug_value(value)
        blackboard = {
            scope: {str(name): self._debug_value(value) for name, value in values.items()}
            for scope, values in self.blackboard.snapshot(self.object_key).items()
        }
        return {
            "nodes": list(dict.fromkeys([*self.executed_nodes, *([self.pause_node] if self.pause_node else [])])),
            "edges": list(dict.fromkeys(self.executed_edges)),
            "values": values,
            "variables": {str(name): self._debug_value(value) for name, value in self.variables.items()},
            "blackboard": blackboard,
            "paused": self.debug_paused,
            "pause_node": self.pause_node,
            "breakpoints": sorted(self.breakpoints),
            "breakpoint_conditions": dict(self.breakpoint_conditions),
            "condition_error": self.debug_condition_error,
            "watches": self._watch_snapshot(),
        }

    def _watch_snapshot(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for expression in self.watch_expressions:
            try:
                result[expression] = self._debug_value(self._evaluate_debug_expression(expression))
            except ValueError as exc:
                result[expression] = f"Erro: {exc}"
        return result

    def _evaluate_debug_expression(self, expression: str) -> Any:
        text = str(expression).strip()
        if not text:
            return True
        parts = re.split(r"\s+(?:ou|or)\s+", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return any(bool(self._evaluate_debug_expression(part)) for part in parts)
        parts = re.split(r"\s+(?:e|and)\s+", text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return all(bool(self._evaluate_debug_expression(part)) for part in parts)
        if text.lower().startswith("não "):
            return not bool(self._evaluate_debug_expression(text[4:]))
        if text.lower().startswith("not "):
            return not bool(self._evaluate_debug_expression(text[4:]))
        match = re.fullmatch(r"(.+?)\s*(==|!=|>=|<=|>|<)\s*(.+)", text)
        if match:
            left = self._debug_operand(match.group(1))
            right = self._debug_operand(match.group(3), bare_text=True)
            operator = match.group(2)
            try:
                if operator == "==":
                    return left == right
                if operator == "!=":
                    return left != right
                if operator == ">":
                    return left > right
                if operator == ">=":
                    return left >= right
                if operator == "<":
                    return left < right
                return left <= right
            except TypeError as exc:
                raise ValueError("os valores comparados têm tipos incompatíveis") from exc
        return self._debug_operand(text)

    def _debug_operand(self, token: str, bare_text: bool = False) -> Any:
        value = str(token).strip()
        lowered = value.lower()
        if "." in value:
            scope, name = value.split(".", 1)
            if scope.lower() in {"object", "objeto", "scene", "cena", "project", "projeto"}:
                normalized_scope = {
                    "objeto": "object", "cena": "scene", "projeto": "project",
                }.get(scope.lower(), scope.lower())
                scoped_value = self.blackboard.get(normalized_scope, name, self.object_key)
                scoped_snapshot = self.blackboard.snapshot(self.object_key).get(normalized_scope, {})
                if name not in scoped_snapshot:
                    raise ValueError(f"variável '{value}' não encontrada")
                return scoped_value
        found = self.blackboard.find(value, self.object_key)
        if found is not None:
            return found[1]
        if lowered in {"true", "verdadeiro"}:
            return True
        if lowered in {"false", "falso"}:
            return False
        if lowered in {"none", "null", "nenhum"}:
            return None
        if lowered == "dt":
            return self._debug_dt
        if lowered in {"x", "y", "w", "h", "rotation", "grounded", "name"}:
            if self._debug_game is None or not hasattr(self._debug_game, lowered):
                raise ValueError(f"'{value}' não está disponível neste objeto")
            return getattr(self._debug_game, lowered)
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            if bare_text:
                return value
            raise ValueError(f"variável '{value}' não encontrada") from None

    @staticmethod
    def _debug_value(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        name = getattr(value, "name", None)
        return f"<{name or type(value).__name__}>"

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
