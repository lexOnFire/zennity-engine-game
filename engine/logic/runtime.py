"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

import ast
import random
import re
from copy import deepcopy
from typing import Any, Callable, Iterator, Mapping

try:
    from .graph_asset import normalize_logic_graph
    from .blackboard import BlackboardStore
    from .event_bus import LogicEvent, LogicEventBus
except ImportError:  # Runtime autocontido exportado.
    from .logic_graph_asset import normalize_logic_graph
    from .logic_blackboard import BlackboardStore
    from .logic_event_bus import LogicEvent, LogicEventBus


class LogicGraphRuntime:
    """Executa fluxo e resolve valores conectados sem depender de Qt/Pygame."""

    MAX_STEPS = 256

    def __init__(
        self,
        graph: Mapping[str, Any],
        blackboard: BlackboardStore | None = None,
        object_key: str = "Object",
        event_bus: LogicEventBus | None = None,
        subgraph_loader: Callable[[str], Mapping[str, Any]] | None = None,
        call_stack: tuple[str, ...] = (),
    ) -> None:
        self.graph = normalize_logic_graph(graph)
        self.object_key = str(object_key)
        self.blackboard = blackboard or BlackboardStore()
        self.blackboard.register(self.graph.get("variables", {}), self.object_key)
        self.event_bus = event_bus or LogicEventBus()
        self.subgraph_loader = subgraph_loader
        self.call_stack = tuple(str(path).casefold() for path in call_stack)
        self.nodes = {node["id"]: node for node in self.graph["nodes"]}
        self.outgoing: dict[str, list[dict[str, Any]]] = {}
        self.incoming: dict[tuple[str, str], dict[str, Any]] = {}
        for edge in self.graph["edges"]:
            self.outgoing.setdefault(edge["from_node"], []).append(edge)
            self.incoming[(str(edge["to_node"]), str(edge.get("to_port", "in")))] = edge
        for edges in self.outgoing.values():
            edges.sort(key=lambda edge: (int(edge.get("order", 0)), str(edge.get("id", ""))))
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
        self._last_game: Any = None
        self._last_dt = 0.0
        self._pending_custom_events: list[tuple[str, LogicEvent]] = []
        self._event_trace_pending = False
        self._subgraph_outputs: dict[str, Any] = {}
        self._timer_elapsed: dict[str, float] = {}
        self._timer_fired: set[str] = set()
        self._node_state: dict[str, dict[str, Any]] = {}
        self._persistent_motion: dict[str, dict[str, Any]] = {}
        self._implicit_target: Any = None
        self.started = False
        for node in self.nodes.values() if not self.call_stack else ():
            if node.get("type") != "event_custom":
                continue
            event_name = str(node.get("properties", {}).get("name", "evento")).strip()
            node_id = str(node["id"])
            self.event_bus.subscribe(event_name, lambda event, wanted=node_id: self._receive_custom_event(wanted, event))

    def run_subgraph(self, game: Any, dt: float, inputs: Mapping[str, Any]) -> dict[str, Any]:
        """Executa uma chamada reutilizável sem iniciar eventos de frame."""
        self.started = True
        self._last_game = game
        self._last_dt = float(dt)
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self._subgraph_outputs.clear()
        for node in self.nodes.values():
            if node.get("type") != "subgraph_input":
                continue
            properties = node.get("properties", {})
            name = str(properties.get("name", "entrada")).strip()
            self._store(str(node["id"]), "value", deepcopy(inputs.get(name, properties.get("default"))))
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node.get("type") == "subgraph_start":
                self.executed_nodes.append(str(node["id"]))
                self._follow(str(node["id"]), "next", game, float(dt), budget, set())
        return deepcopy(self._subgraph_outputs)

    def start(self, game: Any) -> None:
        if self.started:
            return
        self.started = True
        self._last_game = game
        self._last_dt = 0.0
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        if self.breakpoints:
            self._begin_debug_event("event_start", game, 0.0)
        else:
            self._run_event("event_start", game, 0.0)

    def update(self, game: Any, dt: float) -> None:
        self._last_game = game
        self._last_dt = float(dt)
        if not self.started:
            self.start(game)
        if self.debug_paused:
            return
        self._update_timers(game, float(dt))
        self._apply_persistent_motion(float(dt))
        self._run_key_pressed_events(game, float(dt))
        if self.breakpoints:
            if self._debug_generator is None:
                self.values.clear()
                self.executed_nodes.clear()
                self.executed_edges.clear()
                if self._pending_custom_events:
                    node_id, event = self._pending_custom_events.pop(0)
                    self._begin_debug_custom_event(node_id, event)
                else:
                    self._begin_debug_event("event_update", game, float(dt))
            else:
                self._drive_debug()
            return
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        self._run_event("event_update", game, float(dt))

    def _run_key_pressed_events(self, game: Any, dt: float) -> None:
        for node in self.nodes.values():
            if node.get("type") != "event_key_pressed":
                continue
            key = str(node.get("properties", {}).get("key", "D")).strip().lower()
            if game.key_pressed(key):
                self._run_event_node(node, game, dt)

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
        for state in list(self._persistent_motion.values()):
            target = state.get("target")
            if target is None or not bool(getattr(target, "active", True)):
                continue
            self._move_target(target, float(state.get("x", 0.0)), float(state.get("y", 0.0)), dt)

    def trigger_event(self, event_type: str, game: Any, dt: float = 0.0, payload: Any = None) -> None:
        """Dispara um evento físico enviado pelo Play Mode."""
        if not self.started:
            self.start(game)
        self._last_game = game
        self._last_dt = float(dt)
        if self.debug_paused:
            return
        self.values.clear()
        self.executed_nodes.clear()
        self.executed_edges.clear()
        if self.breakpoints:
            self._begin_debug_event(str(event_type), game, float(dt), payload)
        else:
            self._run_event(str(event_type), game, float(dt), payload)

    def _update_timers(self, game: Any, dt: float) -> None:
        for node in self.nodes.values():
            if node.get("type") != "event_timer":
                continue
            node_id = str(node["id"])
            properties = node.get("properties", {})
            repeat = bool(properties.get("repeat", False))
            if node_id in self._timer_fired and not repeat:
                continue
            seconds = max(0.001, float(properties.get("seconds", 1.0)))
            elapsed = self._timer_elapsed.get(node_id, 0.0) + max(0.0, float(dt))
            if elapsed < seconds:
                self._timer_elapsed[node_id] = elapsed
                continue
            self._timer_elapsed[node_id] = elapsed % seconds if repeat else seconds
            self._timer_fired.add(node_id)
            self._run_event_node(node, game, dt)

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
        self._pending_custom_events.clear()
        self._timer_elapsed.clear()
        self._timer_fired.clear()
        self._node_state.clear()
        self._persistent_motion.clear()
        self._implicit_target = None
        self.started = False
        self.start(game)
        if not self.debug_paused:
            self.update(game, float(dt))

    def _begin_debug_event(self, event_type: str, game: Any, dt: float, payload: Any = None) -> None:
        self._debug_game = game
        self._debug_dt = float(dt)
        self._debug_generator = self._debug_event_generator(event_type, game, dt, payload)
        self._debug_waiting_node = None
        self._drive_debug()

    def _begin_debug_custom_event(self, node_id: str, event: LogicEvent) -> None:
        if self._last_game is None:
            return
        self._debug_game = self._last_game
        self._debug_dt = self._last_dt
        self._debug_generator = self._debug_custom_event_generator(node_id, event)
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

    def _debug_event_generator(self, event_type: str, game: Any, dt: float, payload: Any = None) -> Iterator[str]:
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node["type"] != event_type:
                continue
            node_id = str(node["id"])
            yield node_id
            if node_id not in self.executed_nodes:
                self.executed_nodes.append(node_id)
            if payload is not None:
                self._store(node_id, "other", payload)
            yield from self._follow_debug(node_id, "next", game, dt, budget, set())

    def _debug_custom_event_generator(self, node_id: str, event: LogicEvent) -> Iterator[str]:
        node = self.nodes.get(str(node_id))
        if node is None or self._last_game is None:
            return
        yield str(node_id)
        if node_id not in self.executed_nodes:
            self.executed_nodes.append(str(node_id))
        self._store(str(node_id), "payload", deepcopy(event.payload))
        yield from self._follow_debug(str(node_id), "next", self._last_game, self._last_dt, [self.MAX_STEPS], set())

    def _receive_custom_event(self, node_id: str, event: LogicEvent) -> None:
        self._event_trace_pending = True
        if self._last_game is None or self.debug_paused or self._debug_generator is not None:
            self._pending_custom_events.append((str(node_id), event))
            return
        if self.breakpoints:
            self._begin_debug_custom_event(str(node_id), event)
            return
        self._run_custom_event(str(node_id), event)

    def consume_event_trace(self) -> bool:
        pending = self._event_trace_pending
        self._event_trace_pending = False
        return pending

    def _run_custom_event(self, node_id: str, event: LogicEvent) -> None:
        if self._last_game is None or node_id not in self.nodes:
            return
        if node_id not in self.executed_nodes:
            self.executed_nodes.append(node_id)
        self._store(node_id, "payload", deepcopy(event.payload))
        self._follow(node_id, "next", self._last_game, self._last_dt, [self.MAX_STEPS], set())

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
            previous_target = self._implicit_target
            self._implicit_target = self._node_state.get(node_id, {}).get("flow_target", previous_target)
            try:
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
            finally:
                self._implicit_target = previous_target

    def _run_event(self, event_type: str, game: Any, dt: float, payload: Any = None) -> None:
        budget = [self.MAX_STEPS]
        for node in self.nodes.values():
            if node["type"] == event_type:
                if payload is not None:
                    self._store(str(node["id"]), "other", payload)
                self._run_event_node(node, game, dt, budget)

    def _run_event_node(
        self,
        node: Mapping[str, Any],
        game: Any,
        dt: float,
        budget: list[int] | None = None,
    ) -> None:
        node_id = str(node["id"])
        if node_id not in self.executed_nodes:
            self.executed_nodes.append(node_id)
        self._follow(node_id, "next", game, dt, budget or [self.MAX_STEPS], set())

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
            previous_target = self._implicit_target
            self._implicit_target = self._node_state.get(node_id, {}).get("flow_target", previous_target)
            try:
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
            finally:
                self._implicit_target = previous_target

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
        if node_type == "key_held":
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
        if node_type == "move_by":
            target = self._read_target(node_id, game, dt, set())
            velocity_x = float(self._read_input(node_id, "x", properties.get("x", 100.0), game, dt, set()))
            velocity_y = float(self._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
            delta_x, delta_y = velocity_x * dt, velocity_y * dt
            if callable(getattr(target, "move", None)):
                target.move(delta_x, delta_y)
            else:
                target.x = float(target.x) + delta_x
                target.y = float(target.y) + delta_y
            return ["next"]
        if node_type == "start_continuous_motion":
            target = self._read_target(node_id, game, dt, set())
            velocity_x = float(self._read_input(node_id, "x", properties.get("x", 100.0), game, dt, set()))
            velocity_y = float(self._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
            was_active = node_id in self._persistent_motion
            self._persistent_motion[node_id] = {"target": target, "x": velocity_x, "y": velocity_y}
            if not was_active:
                self._move_target(target, velocity_x, velocity_y, dt)
            return ["next"]
        if node_type == "stop_continuous_motion":
            target = self._read_target(node_id, game, dt, set())
            self._persistent_motion = {
                key: state for key, state in self._persistent_motion.items()
                if state.get("target") is not target
            }
            return ["next"]
        if node_type == "patrol_axis":
            target = self._read_target(node_id, game, dt, set())
            axis = str(properties.get("axis", "Y")).strip().lower()
            axis = "x" if axis == "x" else "y"
            minimum = float(self._read_input(node_id, "minimum", properties.get("minimum", -100.0), game, dt, set()))
            maximum = float(self._read_input(node_id, "maximum", properties.get("maximum", 100.0), game, dt, set()))
            if minimum > maximum:
                minimum, maximum = maximum, minimum
            speed = abs(float(self._read_input(node_id, "speed", properties.get("speed", 100.0), game, dt, set())))
            current = float(getattr(target, axis))
            state = self._node_state.setdefault(node_id, {"direction": 1.0})
            direction = float(state.get("direction", 1.0))
            if current >= maximum:
                direction = -1.0
            elif current <= minimum:
                direction = 1.0
            next_position = max(minimum, min(maximum, current + direction * speed * dt))
            delta = next_position - current
            if callable(getattr(target, "move", None)):
                target.move(delta if axis == "x" else 0.0, delta if axis == "y" else 0.0)
            else:
                setattr(target, axis, next_position)
            override_physics = getattr(target, "override_physics_axis", None)
            if callable(override_physics):
                override_physics(axis)
            state["direction"] = direction
            self._store(node_id, "direction", direction)
            self._store(node_id, "position", next_position)
            return ["next"]
        if node_type == "jump":
            force = float(self._read_input(node_id, "force", properties.get("force", 420.0), game, dt, set()))
            game.jump(force)
            return ["next"]
        if node_type == "play_animation":
            state = self._read_input(node_id, "state", properties.get("state", "Idle"), game, dt, set())
            game.animator.play(str(state))
            return ["next"]
        if node_type == "play_animation_asset":
            path = str(self._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
            if path:
                game.play_animation_asset(path)
            return ["next"]
        if node_type == "stop_animation":
            game.stop_animation()
            return ["next"]
        if node_type == "play_sound":
            path = str(self._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
            if path:
                game.play_sound(path)
            return ["next"]
        if node_type == "set_sprite":
            target = self._read_target(node_id, game, dt, set())
            path = str(self._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
            if path:
                target.set_sprite(path)
            return ["next"]
        if node_type == "start_texture_scroll":
            target = self._read_target(node_id, game, dt, set())
            path = str(self._read_input(node_id, "path", properties.get("path", ""), game, dt, set()))
            speed_x = float(self._read_input(node_id, "speed_x", properties.get("speed_x", 0.0), game, dt, set()))
            speed_y = float(self._read_input(node_id, "speed_y", properties.get("speed_y", 80.0), game, dt, set()))
            target.start_texture_scroll(
                speed_x,
                speed_y,
                repeat_x=bool(properties.get("repeat_x", False)),
                repeat_y=bool(properties.get("repeat_y", True)),
                parallax=float(properties.get("parallax", 1.0)),
                image_path=path,
                send_to_background=bool(properties.get("send_to_background", True)),
            )
            return ["next"]
        if node_type == "stop_texture_scroll":
            target = self._read_target(node_id, game, dt, set())
            target.stop_texture_scroll(reset=bool(properties.get("reset", False)))
            return ["next"]
        if node_type == "create_object":
            name = str(self._read_input(node_id, "name", properties.get("name", "NovoObjeto"), game, dt, set()))
            x = float(self._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set()))
            y = float(self._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
            if bool(properties.get("relative", False)):
                x += float(game.x)
                y += float(game.y)
            inherit_source = bool(properties.get("inherit_source", True))
            if inherit_source and callable(getattr(game, "clone_object", None)):
                source = (
                    self._read_input(node_id, "source", game, game, dt, set())
                    if (node_id, "source") in self.incoming
                    else game
                )
                created = game.clone_object(source, name)
                created.x = x
                created.y = y
                created_data = getattr(created, "obj", None)
                if isinstance(created_data, dict) and not bool(properties.get("inherit_logic", False)):
                    created_data["logic_graphs"] = []
            else:
                created = game.create_object(
                    name=name,
                    x=x,
                    y=y,
                    width=float(properties.get("width", 64.0)),
                    height=float(properties.get("height", 64.0)),
                    color=str(properties.get("color", "#58a6ff")),
                    texture=str(properties.get("texture", "")),
                    tag=str(properties.get("tag", "Untagged")),
                )
            self._store(node_id, "object", created)
            self._node_state.setdefault(node_id, {})["flow_target"] = created
            return ["next"]
        if node_type == "create_prefab":
            path = str(properties.get("path", "")).strip()
            if not path:
                raise RuntimeError("Escolha um arquivo .zprefab.")
            x = float(self._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set()))
            y = float(self._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
            if bool(properties.get("relative", False)):
                x += float(game.x)
                y += float(game.y)
            created = game.create_prefab(path, x, y)
            self._store(node_id, "object", created)
            self._node_state.setdefault(node_id, {})["flow_target"] = created
            return ["next"]
        if node_type == "clone_object":
            target = self._read_target(node_id, game, dt, set())
            name = str(self._read_input(node_id, "name", properties.get("name", ""), game, dt, set()))
            created = game.clone_object(target, name)
            self._store(node_id, "object", created)
            self._node_state.setdefault(node_id, {})["flow_target"] = created
            return ["next"]
        if node_type == "add_component":
            target = self._read_target(node_id, game, dt, set())
            component_properties = properties.get("properties", {})
            target.add_component(
                str(properties.get("component", "BoxCollider")),
                component_properties if isinstance(component_properties, Mapping) else {},
            )
            return ["next"]
        if node_type == "remove_component":
            target = self._read_target(node_id, game, dt, set())
            target.remove_component(str(properties.get("component", "BoxCollider")))
            return ["next"]
        if node_type == "set_hud":
            text = self._read_input(node_id, "text", properties.get("text", "Texto"), game, dt, set())
            game.set_hud(f"logic:{node_id}", str(text))
            return ["next"]
        if node_type == "emit_event":
            name = str(properties.get("name", "evento")).strip()
            payload = self._read_input(node_id, "payload", properties.get("payload"), game, dt, set())
            self.event_bus.emit(name, payload, self.object_key)
            return ["next"]
        if node_type == "set_position":
            target = self._read_target(node_id, game, dt, set())
            target.x = float(self._read_input(node_id, "x", properties.get("x", 0.0), game, dt, set()))
            target.y = float(self._read_input(node_id, "y", properties.get("y", 0.0), game, dt, set()))
            return ["next"]
        if node_type == "rotate":
            target = self._read_target(node_id, game, dt, set())
            degrees = float(self._read_input(node_id, "degrees", properties.get("degrees", 90.0), game, dt, set()))
            target.rotation += degrees
            return ["next"]
        if node_type == "set_active":
            target = self._read_target(node_id, game, dt, set())
            target.active = bool(self._read_input(node_id, "active", properties.get("active", True), game, dt, set()))
            return ["next"]
        if node_type == "destroy_object":
            target = self._read_target(node_id, game, dt, set())
            target.destroy()
            return []
        if node_type == "restart_scene":
            game.restart()
            return []
        if node_type == "log_message":
            text = self._read_input(node_id, "text", properties.get("text", "Mensagem"), game, dt, set())
            game.log(str(text))
            return ["next"]
        if node_type == "call_subgraph":
            path = str(properties.get("path", "")).strip()
            if not path or self.subgraph_loader is None:
                raise RuntimeError("Subgrafo não configurado.")
            identity = path.casefold()
            if identity in self.call_stack:
                chain = " → ".join((*self.call_stack, identity))
                raise RuntimeError(f"Referência circular entre subgrafos: {chain}")
            graph = self.subgraph_loader(path)
            declared_inputs = properties.get("inputs", []) if isinstance(properties.get("inputs"), list) else []
            input_values: dict[str, Any] = {}
            for definition in declared_inputs:
                if not isinstance(definition, Mapping):
                    continue
                name = str(definition.get("name", "")).strip()
                if name:
                    input_values[name] = self._read_input(
                        node_id, name, definition.get("default"), game, dt, set()
                    )
            child = LogicGraphRuntime(
                graph,
                self.blackboard,
                self.object_key,
                self.event_bus,
                self.subgraph_loader,
                (*self.call_stack, identity),
            )
            outputs = child.run_subgraph(game, dt, input_values)
            for name, value in outputs.items():
                self._store(node_id, str(name), value)
            return ["next"]
        if node_type == "subgraph_return":
            name = str(properties.get("name", "resultado")).strip()
            value = self._read_input(node_id, "value", properties.get("default"), game, dt, set())
            self._subgraph_outputs[name] = deepcopy(value)
            self._store(node_id, "value", value)
            return []
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
        if node_type == "once":
            state = self._node_state.setdefault(node_id, {"executed": False})
            if bool(state["executed"]):
                return ["blocked"]
            state["executed"] = True
            return ["next"]
        if node_type == "cooldown":
            seconds = max(0.0, float(self._read_input(node_id, "seconds", properties.get("seconds", 1.0), game, dt, set())))
            state = self._node_state.setdefault(node_id, {"remaining": 0.0})
            remaining = max(0.0, float(state.get("remaining", 0.0)) - max(0.0, float(dt)))
            if remaining > 0.0:
                state["remaining"] = remaining
                return ["blocked"]
            state["remaining"] = seconds
            return ["next"]
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

    def _read_target(self, node_id: str, game: Any, dt: float, resolving: set[tuple[str, str]]) -> Any:
        """Resolve uma porta de objeto sem copiar o objeto atual por engano."""
        if (node_id, "target") not in self.incoming:
            return self._implicit_target or game
        return self._read_input(node_id, "target", game, game, dt, resolving) or game

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

        if node_type in {"event_collision_enter", "event_collision_exit", "event_trigger_enter", "event_trigger_exit"}:
            value = deepcopy(self.values.get((node_id, "other")))
        elif node_type == "subgraph_input":
            value = deepcopy(self.values.get((node_id, "value"), properties.get("default")))
        elif node_type == "call_subgraph":
            value = deepcopy(self.values.get((node_id, port)))
        elif node_type == "event_custom":
            value = deepcopy(self.values.get((node_id, "payload")))
        elif node_type == "input_axis":
            negative = str(properties.get("negative", "A")).lower()
            positive = str(properties.get("positive", "D")).lower()
            value = float(game.axis(negative, positive))
            self.values["axis"] = value
        elif node_type == "key_pressed":
            value = bool(game.key_pressed(str(properties.get("key", "space")).lower()))
        elif node_type == "key_held":
            value = bool(game.key(str(properties.get("key", "space")).lower()))
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
        elif node_type == "not":
            value = not bool(self._read_input(node_id, "value", False, game, dt, resolving))
        elif node_type in {"add_number", "subtract_number", "multiply_number", "divide_number"}:
            left = float(self._read_input(node_id, "a", properties.get("a", 0.0), game, dt, resolving))
            right = float(self._read_input(node_id, "b", properties.get("b", 0.0), game, dt, resolving))
            if node_type == "add_number":
                value = left + right
            elif node_type == "subtract_number":
                value = left - right
            elif node_type == "multiply_number":
                value = left * right
            else:
                if right == 0.0:
                    raise RuntimeError("Divisão por zero.")
                value = left / right
        elif node_type == "absolute_number":
            value = abs(float(self._read_input(node_id, "value", properties.get("value", 0.0), game, dt, resolving)))
        elif node_type == "clamp_number":
            raw = float(self._read_input(node_id, "value", properties.get("value", 0.0), game, dt, resolving))
            minimum = float(self._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving))
            maximum = float(self._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving))
            if minimum > maximum:
                minimum, maximum = maximum, minimum
            value = max(minimum, min(maximum, raw))
        elif node_type == "random_number":
            minimum = float(self._read_input(node_id, "minimum", properties.get("minimum", 0.0), game, dt, resolving))
            maximum = float(self._read_input(node_id, "maximum", properties.get("maximum", 1.0), game, dt, resolving))
            value = random.uniform(minimum, maximum)
        elif node_type == "delta_time":
            value = float(dt)
        elif node_type == "join_text":
            left = self._read_input(node_id, "a", properties.get("a", ""), game, dt, resolving)
            right = self._read_input(node_id, "b", properties.get("b", ""), game, dt, resolving)
            value = f"{left}{right}"
        elif node_type == "to_text":
            value = str(self._read_input(node_id, "value", properties.get("value", ""), game, dt, resolving))
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
        elif node_type == "get_position":
            target = self._read_target(node_id, game, dt, resolving)
            value = float(target.x if port == "x" else target.y)
        elif node_type == "find_tag":
            value = game.find(str(properties.get("tag", "Player")))
        elif node_type in {"create_object", "create_prefab", "clone_object"}:
            value = self.values.get((node_id, "object"))
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
            "events": list(self.event_bus.recent[-8:]),
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
