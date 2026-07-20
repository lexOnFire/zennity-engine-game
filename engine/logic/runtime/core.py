"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

import ast
import math
import re
from copy import deepcopy
from typing import Any, Callable, Iterator, Mapping

from .registry import registry
from .output_evaluator import evaluate_output
from . import nodes

try:
    from ..graph_asset import normalize_logic_graph
    from ..blackboard import BlackboardStore
    from ..event_bus import LogicEvent, LogicEventBus
except ImportError:  # Runtime autocontido exportado.
    from ..logic_graph_asset import normalize_logic_graph
    from ..logic_blackboard import BlackboardStore
    from ..logic_event_bus import LogicEvent, LogicEventBus


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
        self._created_event_depth = 0
        self.started = False
        for node in self.nodes.values() if not self.call_stack else ():
            if node.get("type") != "event_custom":
                continue
            event_name = str(node.get("properties", {}).get("name", "event")).strip()
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
            name = str(properties.get("name", "input")).strip()
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
        for key, state in list(self._persistent_motion.items()):
            target = state.get("target")
            if target is None or not bool(getattr(target, "active", True)):
                self._persistent_motion.pop(key, None)
                self._remove_motion_debug(target, key)
                continue
            paused = bool(state.get("paused", False))
            stopping = bool(state.get("stopping", False))
            desired_x = 0.0 if paused or stopping else float(state.get("desired_x", 0.0))
            desired_y = 0.0 if paused or stopping else float(state.get("desired_y", 0.0))
            rate = float(state.get("deceleration" if paused or stopping else "acceleration", 0.0))
            current_x = self._approach(float(state.get("current_x", 0.0)), desired_x, rate, dt)
            current_y = self._approach(float(state.get("current_y", 0.0)), desired_y, rate, dt)
            state["current_x"], state["current_y"] = current_x, current_y
            velocity_x, velocity_y = current_x, current_y
            if str(state.get("space", "global")).lower() == "local":
                radians = math.radians(float(getattr(target, "rotation", 0.0)))
                velocity_x, velocity_y = (
                    current_x * math.cos(radians) - current_y * math.sin(radians),
                    current_x * math.sin(radians) + current_y * math.cos(radians),
                )
            if velocity_x or velocity_y:
                self._move_target(target, velocity_x, velocity_y, dt)
            self._sync_motion_debug(key, state)
            if stopping and abs(current_x) < 1e-6 and abs(current_y) < 1e-6:
                self._persistent_motion.pop(key, None)
                self._remove_motion_debug(target, key)

    @staticmethod
    def _approach(current: float, desired: float, rate: float, dt: float) -> float:
        if rate <= 0.0:
            return desired
        delta = desired - current
        step = max(0.0, rate) * max(0.0, dt)
        if abs(delta) <= step:
            return desired
        return current + math.copysign(step, delta)

    @staticmethod
    def _sync_motion_debug(handle: str, state: Mapping[str, Any]) -> None:
        target = state.get("target")
        update = getattr(target, "update_motion_debug", None)
        if callable(update):
            update(handle, {
                "name": str(state.get("name", "Movement")),
                "x": float(state.get("current_x", 0.0)),
                "y": float(state.get("current_y", 0.0)),
                "target_x": float(state.get("desired_x", 0.0)),
                "target_y": float(state.get("desired_y", 0.0)),
                "space": str(state.get("space", "global")),
                "paused": bool(state.get("paused", False)),
                "stopping": bool(state.get("stopping", False)),
                "graph": str(state.get("graph", "")),
            })

    @staticmethod
    def _remove_motion_debug(target: Any, handle: str) -> None:
        remove = getattr(target, "remove_motion_debug", None)
        if callable(remove):
            remove(handle)

    def _motions_for(self, target: Any, movement: Any = "") -> list[tuple[str, dict[str, Any]]]:
        requested = str(movement or "").strip()
        identity = self._target_identity(target)
        result: list[tuple[str, dict[str, Any]]] = []
        for handle, state in self._persistent_motion.items():
            if self._target_identity(state.get("target")) != identity:
                continue
            if requested and requested not in {handle, str(state.get("name", ""))}:
                continue
            result.append((handle, state))
        return result

    @staticmethod
    def _target_identity(target: Any) -> str:
        raw = getattr(target, "obj", None)
        if isinstance(raw, Mapping):
            return str(raw.get("id", raw.get("name", id(raw))))
        return str(getattr(target, "name", id(target)))

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
            raise RuntimeError("Logic Graph exceeded execution limit; check for loops in the graph.")
        for edge in self.outgoing.get(node_id, []):
            if str(edge.get("from_port", "next")) != port:
                continue
            target_id = str(edge["to_node"])
            if target_id in branch:
                raise RuntimeError("Logic Graph contains an infinite execution loop.")
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
                    raise RuntimeError(f"Node '{target.get('title', target_id)}': {exc}") from exc
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
            raise RuntimeError("Logic Graph exceeded execution limit; check for loops in the graph.")
        for edge in self.outgoing.get(node_id, []):
            if str(edge.get("from_port", "next")) != port:
                continue
            target_id = str(edge["to_node"])
            if target_id in branch:
                raise RuntimeError("Logic Graph contains an infinite execution loop.")
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
                    raise RuntimeError(f"Node '{target.get('title', target_id)}': {exc}") from exc
                next_branch = set(branch)
                next_branch.add(target_id)
                for next_port in next_ports:
                    self._follow(target_id, next_port, game, dt, budget, next_branch)
            finally:
                self._implicit_target = previous_target

    def _execute(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        node_type = str(node["type"])
        executor = registry.executors.get(node_type)
        if executor:
            return executor(self, node, game, dt)
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
            target = self._implicit_target or game
        else:
            target = self._read_input(node_id, "target", game, game, dt, resolving) or game
        self._store(node_id, "Alvo atual", target)
        return target

    def _spawn_group(self, node_id: str) -> str:
        return f"{self.object_key}:{self.graph.get('name', 'LogicGraph')}:{node_id}"

    def _spawn_allowed(self, game: Any, node_id: str, properties: Mapping[str, Any]) -> bool:
        checker = getattr(game, "can_spawn", None)
        if not callable(checker):
            return True
        return bool(checker(self._spawn_group(node_id), int(properties.get("max_instances", 0))))

    def _configure_spawned(
        self,
        game: Any,
        created: Any,
        node_id: str,
        properties: Mapping[str, Any],
        dt: float,
    ) -> None:
        configure = getattr(game, "configure_spawned", None)
        if callable(configure):
            configure(
                created,
                spawn_group=self._spawn_group(node_id),
                lifetime=float(properties.get("lifetime", 0.0)),
                max_distance=float(properties.get("max_distance", 0.0)),
                creator_graph=str(self.graph.get("name", "Logic Graph")),
                creator_node=node_id,
                use_pool=bool(properties.get("use_pool", False)),
            )
        self._emit_object_created(game, created, dt)

    def _emit_object_created(self, game: Any, created: Any, dt: float) -> None:
        """Executa o evento de criação usando a nova instância como alvo implícito."""
        if self._created_event_depth >= 16:
            raise RuntimeError("Muitos objetos foram criados em cascata pelo evento de criação.")
        self._created_event_depth += 1
        previous_target = self._implicit_target
        self._implicit_target = created
        try:
            for node in self.nodes.values():
                if node.get("type") != "event_object_created":
                    continue
                node_id = str(node["id"])
                self._store(node_id, "object", created)
                self._node_state.setdefault(node_id, {})["flow_target"] = created
                self._run_event_node(node, game, dt)
        finally:
            self._implicit_target = previous_target
            self._created_event_depth -= 1

    def _evaluate_output(
        self,
        node_id: str,
        port: str,
        game: Any,
        dt: float,
        resolving: set[tuple[str, str]],
    ) -> Any:
        return evaluate_output(self, node_id, port, game, dt, resolving)

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
                raise ValueError("compared values have incompatible types") from exc
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
                    raise ValueError(f"variable '{value}' not found")
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
                raise ValueError(f"'{value}' is not available on this object")
            return getattr(self._debug_game, lowered)
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            if bare_text:
                return value
            raise ValueError(f"variable '{value}' not found") from None

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
