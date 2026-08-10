"""Mixin de execução e fluxo de controle para ``LogicGraphRuntime``."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterator, Mapping

from .output_evaluator import evaluate_output

try:
    from ..event_bus import LogicEvent
except ImportError:
    from ..logic_event_bus import LogicEvent


class LogicGraphExecutionMixin:
    """Métodos auxiliares de fluxo de controle, eventos e avaliação do grafo."""

    def _handle_animation_finished(
        self,
        node_id: str,
        event: LogicEvent,
        animation_name_filter: str,
    ) -> None:
        """Handle animation finished event received from bus."""
        if event.payload is None or not isinstance(event.payload, dict):
            return

        animation_name = str(event.payload.get("animation_name", "")).strip()
        if animation_name_filter and animation_name != animation_name_filter:
            return

        self.values[(node_id, "owner_object")] = event.payload.get("owner_object")
        self.values[(node_id, "animation_name")] = animation_name
        self.values[(node_id, "elapsed_time")] = float(event.payload.get("elapsed_time", 0.0))

        if node_id not in self.executed_nodes:
            self.executed_nodes.append(node_id)
            for edge in self.outgoing.get(node_id, []):
                if edge.get("from_port") == "exec":
                    self._run_edge(edge, self._last_game, self._last_dt)

    def _handle_ui_button_clicked(self, node_id: str, event: LogicEvent, target_widget_filter: str) -> None:
        """Process UI button click event for ui.button_clicked nodes."""
        if event.payload is None or not isinstance(event.payload, dict):
            return
        widget_name = str(event.payload.get("widget_name") or event.payload.get("button") or "").strip()
        if target_widget_filter and widget_name.lower() != target_widget_filter.lower():
            return

        self._store(node_id, "other", deepcopy(event.payload))
        self._store(node_id, "payload", deepcopy(event.payload))
        self._store(node_id, "widget_name", widget_name)

        if self._last_game is not None:
            if node_id not in self.executed_nodes:
                self.executed_nodes.append(node_id)
            budget = [self.MAX_STEPS]
            self._follow(node_id, "clicked", self._last_game, self._last_dt, budget, set())
            self._follow(node_id, "next", self._last_game, self._last_dt, budget, set())
            self._follow(node_id, "exec", self._last_game, self._last_dt, budget, set())

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
        """Handle physics events from PhysicsWorld."""
        if game_object is None or method_name not in ("on_collision_enter", "on_collision_exit", "on_trigger_enter", "on_trigger_exit"):
            return

        if self._last_game is None:
            return

        owner_name = getattr(game_object, "name", None)
        if owner_name != self.object_key:
            return

        event_type_map = {
            "on_collision_enter": "on_collision_enter",
            "on_collision_exit": "on_collision_exit",
            "on_trigger_enter": "on_trigger_enter",
            "on_trigger_exit": "on_trigger_exit",
        }

        event_type_id = event_type_map.get(method_name)
        if event_type_id is None:
            return

        other_object = getattr(other_collider, "game_object", None)

        for node in self.nodes.values():
            if node.get("type") != event_type_id:
                continue

            node_id = str(node["id"])
            if node_id not in self.executed_nodes:
                self.executed_nodes.append(node_id)

            self._store(node_id, "other", other_object)
            self._store(node_id, "self_object", game_object)
            self._store(node_id, "other_object", other_object)
            self._store(node_id, "self_collider", None)
            self._store(node_id, "other_collider", other_collider)
            self._store(node_id, "is_trigger", bool(getattr(other_collider, "is_trigger", False)))

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

        from engine.core.context import EngineContext
        from engine.metadata.manager import MetadataManager
        from engine.core.metadata.node import NodeDefinition
        from .registry import registry

        context = EngineContext.current()
        if context:
            manager = context.services.get_optional(MetadataManager)
            if manager:
                node_def = manager.get(NodeDefinition, node_type)
                if node_def and node_def.executor:
                    return node_def.executor(self, node, game, dt)

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
        self.values[node_id] = value
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
