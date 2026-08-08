"""Executor leve e tipado dos grafos visuais ``.zlogic``."""

from __future__ import annotations

import ast
import math
import random
import re
import sys
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

# Phase 5B.2: Import physics event dispatch
from .physics_event_dispatch import register_physics_event_handler, dispatch_physics_event

# Phase 7B.1: Import registry for dispatcher consolidation
from .runtime.registry import registry


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

        # Phase 5B.2: Register physics event handler if not a subgraph
        if not self.call_stack:
            register_physics_event_handler(self._handle_physics_event)

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

    def _handle_physics_event(self, game_object: Any, method_name: str, other_collider: Any) -> None:
        """Phase 5B.2: Handle physics events from PhysicsWorld.

        Called when PhysicsWorld emits collision/trigger events.
        Routes events to appropriate event nodes based on owner.
        """
        if game_object is None or method_name not in ("on_collision_enter", "on_collision_exit", "on_trigger_enter", "on_trigger_exit"):
            return

        # Ensure last game is set (event might come during update)
        if self._last_game is None:
            return

        # Get the object name to match against owner
        owner_name = getattr(game_object, "name", None)
        if owner_name != self.object_key:
            return

        # Map method name to event type ID and event name
        event_type_map = {
            "on_collision_enter": ("on_collision_enter", "collision_enter"),
            "on_collision_exit": ("on_collision_exit", "collision_exit"),
            "on_trigger_enter": ("on_trigger_enter", "trigger_enter"),
            "on_trigger_exit": ("on_trigger_exit", "trigger_exit"),
        }

        event_type_id, event_name = event_type_map.get(method_name, (None, None))
        if event_type_id is None:
            return

        # Build payload with full collision data
        other_object = getattr(other_collider, "game_object", None)
        payload = {
            "self_object": game_object,
            "other_object": other_object,
            "self_collider": None,  # Will be set when we know which collider on self
            "other_collider": other_collider,
            "is_trigger": bool(getattr(other_collider, "is_trigger", False)),
        }

        # Fire event nodes
        for node in self.nodes.values():
            if node.get("type") != event_type_id:
                continue

            node_id = str(node["id"])
            if node_id not in self.executed_nodes:
                self.executed_nodes.append(node_id)

            # Store payload data for evaluation
            self._store(node_id, "other", other_object)
            self._store(node_id, "self_object", game_object)
            self._store(node_id, "other_object", other_object)
            self._store(node_id, "self_collider", None)
            self._store(node_id, "other_collider", other_collider)
            self._store(node_id, "is_trigger", payload["is_trigger"])

            # Execute the event node's flow
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

    def _try_registry_executor(
        self,
        node: Mapping[str, Any],
        game: Any,
        dt: float
    ) -> tuple[bool, list[str] | None]:
        """
        Try executing node via registry executor (Phase 7B.1).

        Strict contract enforcement:
        - Executor must return list[str]
        - No magic conversions
        - No silent failures

        Returns:
            (found, ports): (True, ports_list) if executor exists and succeeds
                           (False, None) if no executor registered
        """
        node_type = str(node["type"])
        executor = registry.executors.get(node_type)

        if executor is None:
            return False, None

        try:
            ports = executor(self, node, game, dt)

            # Strict type checking: must be list[str]
            if not isinstance(ports, list):
                node_id = str(node.get("id", "unknown"))
                print(
                    f"[LogicRuntime CONTRACT ERROR] Executor for '{node_type}' "
                    f"(node_id={node_id}) returned {type(ports).__name__} "
                    f"instead of list[str]. Got: {repr(ports)}",
                    file=sys.stderr
                )
                return True, None  # Found but invalid contract

            # Validate each port is a string
            for port in ports:
                if not isinstance(port, str):
                    node_id = str(node.get("id", "unknown"))
                    print(
                        f"[LogicRuntime CONTRACT ERROR] Executor for '{node_type}' "
                        f"(node_id={node_id}) returned port {repr(port)} "
                        f"(type {type(port).__name__}) - must be str",
                        file=sys.stderr
                    )
                    return True, None

            return True, ports

        except Exception as e:
            # Programming error - not gameplay failure
            node_id = str(node.get("id", "unknown"))
            import traceback
            print(
                f"[LogicRuntime EXECUTOR ERROR]\n"
                f"  Node: {node_type} (id={node_id})\n"
                f"  Exception: {type(e).__name__}: {e}\n"
                f"  {traceback.format_exc()}",
                file=sys.stderr
            )
            return True, None  # Found but failed

    def _get_node_definition(self, node_type: str) -> Mapping[str, Any] | None:
        """Get canonical node definition from registry."""
        try:
            from .node_definitions.registry import node_registry
            return node_registry.definitions.get(node_type)
        except Exception:
            return None

    def _validate_returned_ports(
        self,
        node_type: str,
        node_id: str,
        returned_ports: list[str]
    ) -> bool:
        """
        Validate returned ports match node definition (Phase 7B.1).

        Returns:
            True if valid, False if invalid
        """
        node_def = self._get_node_definition(node_type)
        if node_def is None:
            # No definition found, can't validate
            return True

        declared_outputs = {
            output["id"] for output in node_def.get("outputs", [])
        }

        for port in returned_ports:
            if port not in declared_outputs:
                print(
                    f"[LogicRuntime PORT ERROR] Executor for '{node_type}' "
                    f"(id={node_id}) returned invalid port '{port}'. "
                    f"Declared outputs: {declared_outputs}",
                    file=sys.stderr
                )
                return False

        return True

    def _is_event_source_node(self, node_type: str) -> bool:
        """
        Check if node is an event source (not actionable).

        Uses node definition metadata, not prefixes.
        """
        node_def = self._get_node_definition(node_type)
        if node_def is None:
            return False

        return node_def.get("kind") == "EVENT" or node_type in {
            "event_custom",
            "event_collision_enter",
            "event_collision_exit",
            "event_trigger_enter",
            "event_trigger_exit",
            "on_animation_event",
            "on_animation_finished",
            "on_collision_enter",
            "on_collision_exit",
        }

    def _is_special_runtime_node(self, node_type: str) -> bool:
        """
        Check if node requires special runtime handling.

        Explicit list only - no prefix-based guessing.
        """
        return node_type in {
            # Subgraph lifecycle
            "call_subgraph",
            "subgraph_input",
            "subgraph_return",
        }

    def _execute_special_node(
        self,
        node: Mapping[str, Any],
        game: Any,
        dt: float
    ) -> list[str]:
        """
        Handle special runtime nodes (Phase 7B.1).

        Preserves original hardcoded logic for nodes with special semantics.
        """
        node_type = str(node["type"])
        node_id = str(node.get("id", "unknown"))
        properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}

        # ========== SUBGRAPH NODES ==========
        if node_type == "subgraph_input":
            return []

        if node_type == "subgraph_return":
            return []

        if node_type == "call_subgraph":
            # Preserved hardcoded logic (original semantics)
            subgraph_id = str(properties.get("graph_id", ""))
            target = self._read_target(node_id, game, dt, set())

            if subgraph_id in self.graphs:
                subgraph = self.graphs[subgraph_id]

                prev_target = self._implicit_target
                self._implicit_target = target

                try:
                    for entry_id in subgraph.entry_nodes:
                        self._follow(entry_id, "exec", game, dt, 1000, set())
                except Exception as e:
                    print(
                        f"[LogicRuntime SUBGRAPH ERROR] Failed executing subgraph "
                        f"{subgraph_id}: {e}",
                        file=sys.stderr
                    )
                finally:
                    self._implicit_target = prev_target

                return ["next"]
            else:
                return ["failure"]

        # Event nodes return empty (handled by event system)
        if self._is_event_source_node(node_type):
            return []

        # Unknown special node
        print(
            f"[LogicRuntime ERROR] Unknown special node type: {node_type} "
            f"(id={node_id})",
            file=sys.stderr
        )
        return ["failure"]

    def _execute(self, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
        """
        Execute a Logic Graph node (Phase 7B.1 - Registry Dispatcher Consolidation).

        Dispatch order:
        1. Registry executor (primary) - now serves 71 registered executors
        2. Special runtime nodes (secondary) - subgraph + event source nodes only
        3. Error diagnosis (fallback) - clear diagnostic messages

        Returns:
            List of output port names for execution to follow
        """
        node_type = str(node["type"])
        node_id = str(node.get("id", "unknown"))

        # ===== PRIMARY PATH: Registry Executor =====
        found, ports = self._try_registry_executor(node, game, dt)

        if found:
            # Executor was found in registry
            if ports is None:
                # Contract violation or programming exception occurred
                # Return failure (don't follow unknown paths)
                return ["failure"]

            # Executor returned ports - validate against node definition
            if not self._validate_returned_ports(node_type, node_id, ports):
                # Returned port doesn't match declaration
                return ["failure"]

            return ports

        # ===== SECONDARY PATH: Special Runtime Nodes =====
        if self._is_special_runtime_node(node_type):
            return self._execute_special_node(node, game, dt)

        # ===== ERROR PATH: Unknown Node =====
        print(
            f"[LogicRuntime FATAL] Unknown node type '{node_type}' (id={node_id}). "
            f"Not in registry and not a special node. Flow halted.",
            file=sys.stderr
        )
        return ["failure"]

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
            # Referências de objetos do Play Mode não podem ser copiadas: elas
            # carregam o mundo e a fila de eventos do processo da viewport.
            value = self.values.get((node_id, "other"))
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
        elif node_type == "compare_text":
            left = self._read_input(node_id, "value", "", game, dt, resolving)
            right = str(properties.get("value", ""))
            operator = str(properties.get("operator", "=="))
            equal = str(left).casefold() == right.casefold()
            value = not equal if operator == "!=" else equal
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
        elif node_type == "get_tag":
            target = self._read_target(node_id, game, dt, resolving)
            value = str(getattr(target, "tag", "Untagged"))
        elif node_type == "get_prefab_parameter":
            target = self._read_target(node_id, game, dt, resolving)
            getter = getattr(target, "prefab_parameter", None)
            name = str(properties.get("name", "speed"))
            value = getter(name, properties.get("default")) if callable(getter) else properties.get("default")
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
