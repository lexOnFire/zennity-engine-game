"""Runtime executável para Behavior Trees da Zennity Engine.

Faz a árvore de comportamento ser EXECUTADA em tempo real no jogo.
Interpreta os nós, gera eventos e gerencia estado da árvore.

Uso básico:
    tree_data = load_json("Assets/Behaviors/Enemy.zbehavior")
    runtime = BehaviorTreeRuntime(tree_data, game_object=enemy)
    runtime.update(dt=0.016)  # a cada frame
    runtime.set_parameter("player_distance", 50)
"""

from __future__ import annotations

import json
import random
import time
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping


class BehaviorStatus(Enum):
    """Status de execução de um nó."""
    RUNNING = "RUNNING"    # Continua executando
    SUCCESS = "SUCCESS"    # Sucesso
    FAILURE = "FAILURE"    # Falhou


class BehaviorTreeRuntime:
    """Runtime que executa uma Behavior Tree.

    Mantém estado dos nós, avalia condições, e controla o fluxo da árvore.
    """

    def __init__(
        self,
        tree_data: Mapping[str, Any],
        game_object: Any = None,
        parameters: Mapping[str, Any] | None = None,
    ) -> None:
        self.tree = dict(tree_data)
        self.game_object = game_object
        self.parameters = dict(parameters or {})

        self._start_time = time.time()
        self._node_timers: dict[str, float] = {}
        self._node_counters: dict[str, int] = {}
        self._active_nodes: set[str] = set()
        self._events: list[dict[str, Any]] = []

    @property
    def events(self) -> list[dict[str, Any]]:
        """Eventos disparados na última update."""
        return self._events

    def clear_events(self) -> None:
        """Limpa fila de eventos."""
        self._events.clear()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────

    def update(self, dt: float = 0.016) -> BehaviorStatus:
        """Atualiza a árvore. Retorna status geral da árvore.

        Args:
            dt: delta time (tempo desde última frame)

        Returns:
            Status geral (RUNNING, SUCCESS, ou FAILURE)
        """
        self.clear_events()
        start_node_id = self.tree.get("start_node")
        if not start_node_id:
            return BehaviorStatus.FAILURE

        status = self._tick_node(start_node_id, dt)
        return status

    def set_parameter(self, name: str, value: Any) -> None:
        """Define um parâmetro (visível para condições)."""
        self.parameters[name] = value
        self._emit_event("parameter_set", parameter=name, value=value)

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Lê um parâmetro."""
        return self.parameters.get(name, default)

    def has_parameter(self, name: str) -> bool:
        """Verifica se parâmetro existe."""
        return name in self.parameters

    # ─────────────────────────────────────────────────────────────────────────
    # NODOS COMPOSTOS
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_sequence(self, node_id: str, children: list[str], dt: float) -> BehaviorStatus:
        """Executa filhos EM ORDEM. Falha se qualquer um falhar."""
        for child_id in children:
            status = self._tick_node(child_id, dt)
            if status == BehaviorStatus.FAILURE:
                self._emit_event("node_failed", node_id=node_id, reason="sequence_child_failed")
                return BehaviorStatus.FAILURE
            if status == BehaviorStatus.RUNNING:
                return BehaviorStatus.RUNNING
        self._emit_event("node_success", node_id=node_id, node_type="sequence")
        return BehaviorStatus.SUCCESS

    def _tick_selector(self, node_id: str, children: list[str], dt: float) -> BehaviorStatus:
        """Tenta filhos até um ter SUCESSO. Falha se todos falharem."""
        for child_id in children:
            status = self._tick_node(child_id, dt)
            if status == BehaviorStatus.SUCCESS:
                self._emit_event("node_success", node_id=node_id, node_type="selector")
                return BehaviorStatus.SUCCESS
            if status == BehaviorStatus.RUNNING:
                return BehaviorStatus.RUNNING
        self._emit_event("node_failed", node_id=node_id, reason="all_options_failed")
        return BehaviorStatus.FAILURE

    # ─────────────────────────────────────────────────────────────────────────
    # DECORADORES
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_repeat(
        self, node_id: str, child_id: str, count: int, dt: float
    ) -> BehaviorStatus:
        """Repete filho N vezes (0 = infinitamente)."""
        counter = self._node_counters.get(node_id, 0)

        if count > 0 and counter >= count:
            self._node_counters[node_id] = 0
            self._emit_event("node_success", node_id=node_id, node_type="repeat")
            return BehaviorStatus.SUCCESS

        status = self._tick_node(child_id, dt)
        if status == BehaviorStatus.SUCCESS:
            self._node_counters[node_id] = counter + 1
            if count == 0:
                return BehaviorStatus.RUNNING
            if counter + 1 >= count:
                self._node_counters[node_id] = 0
                self._emit_event("node_success", node_id=node_id, node_type="repeat")
                return BehaviorStatus.SUCCESS
            return BehaviorStatus.RUNNING

        return status

    def _tick_cooldown(self, node_id: str, child_id: str, seconds: float, dt: float) -> BehaviorStatus:
        """Aguarda N segundos antes de deixar filho executar novamente."""
        last_run = self._node_timers.get(node_id, 0.0)
        now = time.time()

        if now - last_run < seconds:
            return BehaviorStatus.RUNNING

        self._node_timers[node_id] = now
        status = self._tick_node(child_id, dt)
        return status

    def _tick_limiter(
        self, node_id: str, child_id: str, max_count: int, dt: float
    ) -> BehaviorStatus:
        """Executa filho até N vezes. Depois falha sempre."""
        counter = self._node_counters.get(node_id, 0)

        if counter >= max_count:
            self._emit_event("node_failed", node_id=node_id, reason="limiter_exceeded")
            return BehaviorStatus.FAILURE

        status = self._tick_node(child_id, dt)
        if status != BehaviorStatus.FAILURE:
            self._node_counters[node_id] = counter + 1

        return status

    def _tick_inverter(self, node_id: str, child_id: str, dt: float) -> BehaviorStatus:
        """Inverte resultado: sucesso→falha, falha→sucesso."""
        status = self._tick_node(child_id, dt)

        if status == BehaviorStatus.SUCCESS:
            self._emit_event("node_inverted", node_id=node_id, was="success")
            return BehaviorStatus.FAILURE
        if status == BehaviorStatus.FAILURE:
            self._emit_event("node_inverted", node_id=node_id, was="failure")
            return BehaviorStatus.SUCCESS

        return status

    # ─────────────────────────────────────────────────────────────────────────
    # CONDIÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_target_in_range(
        self, node_id: str, target_tag: str, distance: float, dt: float
    ) -> BehaviorStatus:
        """Checa se alvo (por tag) está dentro do alcance."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        targets = self._find_objects_by_tag(target_tag)
        if not targets:
            self._emit_event("node_failed", node_id=node_id, reason="target_not_found")
            return BehaviorStatus.FAILURE

        my_pos = self._get_position(self.game_object)
        for target in targets:
            target_pos = self._get_position(target)
            dist = self._distance(my_pos, target_pos)
            if dist <= distance:
                self._emit_event("node_success", node_id=node_id, node_type="target_check", distance=dist)
                return BehaviorStatus.SUCCESS

        self._emit_event("node_failed", node_id=node_id, reason="target_out_of_range")
        return BehaviorStatus.FAILURE

    def _tick_health_check(self, node_id: str, min_health: float, dt: float) -> BehaviorStatus:
        """Checa se saúde > valor."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        health = self._get_health(self.game_object)
        if health > min_health:
            self._emit_event("node_success", node_id=node_id, node_type="health_check", health=health)
            return BehaviorStatus.SUCCESS

        self._emit_event("node_failed", node_id=node_id, reason="low_health", health=health)
        return BehaviorStatus.FAILURE

    def _tick_parameter_check(
        self, node_id: str, parameter: str, operator: str, value: Any, dt: float
    ) -> BehaviorStatus:
        """Compara parâmetro com valor."""
        current = self.parameters.get(parameter)

        try:
            if operator == "==":
                success = current == value
            elif operator == "!=":
                success = current != value
            elif operator == "<":
                success = float(current) < float(value)
            elif operator == "<=":
                success = float(current) <= float(value)
            elif operator == ">":
                success = float(current) > float(value)
            elif operator == ">=":
                success = float(current) >= float(value)
            else:
                success = False
        except (TypeError, ValueError):
            success = False

        if success:
            self._emit_event("node_success", node_id=node_id, node_type="parameter_check")
            return BehaviorStatus.SUCCESS

        self._emit_event("node_failed", node_id=node_id, reason="condition_not_met")
        return BehaviorStatus.FAILURE

    def _tick_random_chance(self, node_id: str, chance: float, dt: float) -> BehaviorStatus:
        """Sucesso aleatório."""
        if random.random() * 100 < chance:
            self._emit_event("node_success", node_id=node_id, node_type="random_chance")
            return BehaviorStatus.SUCCESS

        self._emit_event("node_failed", node_id=node_id, reason="random_failed")
        return BehaviorStatus.FAILURE

    # ─────────────────────────────────────────────────────────────────────────
    # AÇÕES
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_idle(self, node_id: str, duration: float, dt: float) -> BehaviorStatus:
        """Espera N segundos."""
        last_start = self._node_timers.get(node_id)
        if last_start is None:
            self._node_timers[node_id] = time.time()
            self._emit_event("action_start", node_id=node_id, action_type="idle")
            return BehaviorStatus.RUNNING

        elapsed = time.time() - last_start
        if elapsed >= duration:
            del self._node_timers[node_id]
            self._emit_event("action_done", node_id=node_id, action_type="idle")
            return BehaviorStatus.SUCCESS

        return BehaviorStatus.RUNNING

    def _tick_patrol(
        self, node_id: str, point_a: tuple[float, float], point_b: tuple[float, float],
        speed: float, dt: float
    ) -> BehaviorStatus:
        """Patrulha entre dois pontos."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        if node_id not in self._active_nodes:
            self._active_nodes.add(node_id)
            self._emit_event("action_start", node_id=node_id, action_type="patrol")

        self._move_towards(self.game_object, point_a, point_b, speed, node_id)
        return BehaviorStatus.RUNNING

    def _tick_chase(
        self, node_id: str, target_tag: str, speed: float, stop_distance: float, dt: float
    ) -> BehaviorStatus:
        """Persegue alvo."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        targets = self._find_objects_by_tag(target_tag)
        if not targets:
            self._emit_event("action_failed", node_id=node_id, action_type="chase", reason="target_lost")
            return BehaviorStatus.FAILURE

        target = targets[0]
        my_pos = self._get_position(self.game_object)
        target_pos = self._get_position(target)
        dist = self._distance(my_pos, target_pos)

        if dist <= stop_distance:
            self._emit_event("action_done", node_id=node_id, action_type="chase")
            return BehaviorStatus.SUCCESS

        self._move_towards_target(self.game_object, target_pos, speed)
        self._emit_event("action_running", node_id=node_id, action_type="chase", distance=dist)
        return BehaviorStatus.RUNNING

    def _tick_move_to(
        self, node_id: str, target_pos: tuple[float, float], speed: float, dt: float
    ) -> BehaviorStatus:
        """Move para posição."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        my_pos = self._get_position(self.game_object)
        dist = self._distance(my_pos, target_pos)

        if dist < 5:
            self._emit_event("action_done", node_id=node_id, action_type="move_to")
            return BehaviorStatus.SUCCESS

        self._move_towards_target(self.game_object, target_pos, speed)
        return BehaviorStatus.RUNNING

    def _tick_attack(
        self, node_id: str, target_tag: str, damage: float, range_val: float, dt: float
    ) -> BehaviorStatus:
        """Ataca alvo."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        targets = self._find_objects_by_tag(target_tag)
        if not targets:
            return BehaviorStatus.FAILURE

        target = targets[0]
        my_pos = self._get_position(self.game_object)
        target_pos = self._get_position(target)
        dist = self._distance(my_pos, target_pos)

        if dist > range_val:
            return BehaviorStatus.FAILURE

        self._apply_damage(target, damage)
        self._emit_event("action_done", node_id=node_id, action_type="attack", damage=damage)
        return BehaviorStatus.SUCCESS

    def _tick_play_animation(self, node_id: str, animation: str, dt: float) -> BehaviorStatus:
        """Toca animação."""
        if not self.game_object:
            return BehaviorStatus.FAILURE

        self._play_animation(self.game_object, animation)
        self._emit_event("action_done", node_id=node_id, action_type="play_animation", animation=animation)
        return BehaviorStatus.SUCCESS

    def _tick_set_parameter(self, node_id: str, parameter: str, value: Any, dt: float) -> BehaviorStatus:
        """Define parâmetro."""
        self.set_parameter(parameter, value)
        self._emit_event("action_done", node_id=node_id, action_type="set_parameter")
        return BehaviorStatus.SUCCESS

    def _tick_log(self, node_id: str, message: str, dt: float) -> BehaviorStatus:
        """Log debug."""
        print(f"[BehaviorTree] {message}")
        self._emit_event("action_done", node_id=node_id, action_type="log")
        return BehaviorStatus.SUCCESS

    # ─────────────────────────────────────────────────────────────────────────
    # SISTEMA INTERNO
    # ─────────────────────────────────────────────────────────────────────────

    def _tick_node(self, node_id: str, dt: float) -> BehaviorStatus:
        """Tick um nó individual."""
        node = self.tree.get("nodes", {}).get(node_id)
        if not node:
            return BehaviorStatus.FAILURE

        node_type = node.get("type", "")

        if node_type == "bt.sequence":
            children = node.get("children", [])
            return self._tick_sequence(node_id, children, dt)

        if node_type == "bt.selector":
            children = node.get("children", [])
            return self._tick_selector(node_id, children, dt)

        if node_type == "bt.repeat":
            child = node.get("child", "")
            count = node.get("count", 0)
            return self._tick_repeat(node_id, child, count, dt)

        if node_type == "bt.cooldown":
            child = node.get("child", "")
            seconds = node.get("seconds", 1.0)
            return self._tick_cooldown(node_id, child, seconds, dt)

        if node_type == "bt.limiter":
            child = node.get("child", "")
            max_count = node.get("max_count", 3)
            return self._tick_limiter(node_id, child, max_count, dt)

        if node_type == "bt.inverter":
            child = node.get("child", "")
            return self._tick_inverter(node_id, child, dt)

        if node_type == "bt.target_in_range":
            target = node.get("target", "Player")
            distance = node.get("distance", 200.0)
            return self._tick_target_in_range(node_id, target, distance, dt)

        if node_type == "bt.health_check":
            min_health = node.get("min_health", 30.0)
            return self._tick_health_check(node_id, min_health, dt)

        if node_type == "bt.parameter_check":
            parameter = node.get("parameter", "")
            operator = node.get("operator", "==")
            value = node.get("value", "")
            return self._tick_parameter_check(node_id, parameter, operator, value, dt)

        if node_type == "bt.random_chance":
            chance = node.get("chance", 50.0)
            return self._tick_random_chance(node_id, chance, dt)

        if node_type == "bt.idle":
            duration = node.get("duration", 1.0)
            return self._tick_idle(node_id, duration, dt)

        if node_type == "bt.patrol":
            point_a = self._parse_vector2(node.get("point_a", (0, 0)))
            point_b = self._parse_vector2(node.get("point_b", (200, 0)))
            speed = node.get("speed", 80.0)
            return self._tick_patrol(node_id, point_a, point_b, speed, dt)

        if node_type == "bt.chase":
            target = node.get("target", "Player")
            speed = node.get("speed", 120.0)
            stop_distance = node.get("stop_distance", 48.0)
            return self._tick_chase(node_id, target, speed, stop_distance, dt)

        if node_type == "bt.move_to":
            target_pos = self._parse_vector2(node.get("target_pos", (0, 0)))
            speed = node.get("speed", 100.0)
            return self._tick_move_to(node_id, target_pos, speed, dt)

        if node_type == "bt.attack":
            target = node.get("target", "Player")
            damage = node.get("damage", 10.0)
            range_val = node.get("range", 64.0)
            return self._tick_attack(node_id, target, damage, range_val, dt)

        if node_type == "bt.play_animation":
            animation = node.get("animation", "Idle")
            return self._tick_play_animation(node_id, animation, dt)

        if node_type == "bt.set_parameter":
            parameter = node.get("parameter", "")
            value = node.get("value", "")
            return self._tick_set_parameter(node_id, parameter, value, dt)

        if node_type == "bt.set_ui_text":
            widget = str(node.get("widget", "quantidade"))
            text = str(node.get("text", "100"))
            return self._tick_set_ui_text(node_id, widget, text, dt)

        if node_type == "bt.set_ui_progress":
            widget = str(node.get("widget", "hp_bar"))
            value = float(node.get("value", 100.0))
            return self._tick_set_ui_progress(node_id, widget, value, dt)

        if node_type == "bt.set_ui_visible":
            widget = str(node.get("widget", "Ui_comida"))
            visible = bool(node.get("visible", True))
            return self._tick_set_ui_visible(node_id, widget, visible, dt)

        if node_type == "bt.decrement_ui_value":
            widget = str(node.get("widget", "quantidade"))
            amount = float(node.get("amount", 1.0))
            return self._tick_decrement_ui_value(node_id, widget, amount, dt)

        if node_type == "bt.increment_ui_value":
            widget = str(node.get("widget", "quantidade"))
            amount = float(node.get("amount", 1.0))
            return self._tick_increment_ui_value(node_id, widget, amount, dt)

        if node_type == "bt.log":
            message = node.get("message", "Debug")
            return self._tick_log(node_id, message, dt)

        return BehaviorStatus.FAILURE

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS (SOBRESCREVER PARA INTEGRAR COM SEU JOGO)
    # ─────────────────────────────────────────────────────────────────────────

    def _find_objects_by_tag(self, tag: str) -> list[Any]:
        """Encontra objetos por tag. SOBRESCREVA ISSO."""
        return []

    def _get_position(self, obj: Any) -> tuple[float, float]:
        """Retorna posição de um objeto. SOBRESCREVA ISSO."""
        if hasattr(obj, "position"):
            return tuple(obj.position)[:2]
        if hasattr(obj, "rect") and hasattr(obj.rect, "center"):
            return obj.rect.center
        return (0.0, 0.0)

    def _get_health(self, obj: Any) -> float:
        """Retorna saúde de um objeto. SOBRESCREVA ISSO."""
        return getattr(obj, "health", 100.0)

    def _move_towards(
        self, obj: Any, point_a: tuple[float, float], point_b: tuple[float, float],
        speed: float, node_id: str
    ) -> None:
        """Alterna movimento entre dois pontos. SOBRESCREVA ISSO."""
        pass

    def _move_towards_target(self, obj: Any, target_pos: tuple[float, float], speed: float) -> None:
        """Move em direção a uma posição. SOBRESCREVA ISSO."""
        pass

    def _apply_damage(self, obj: Any, damage: float) -> None:
        """Aplica dano a um objeto. SOBRESCREVA ISSO."""
        pass

    def _tick_set_ui_text(self, node_id: str, widget: str, text: str, dt: float) -> BehaviorStatus:
        self._set_ui_text(widget, text)
        return BehaviorStatus.SUCCESS

    def _tick_set_ui_progress(self, node_id: str, widget: str, value: float, dt: float) -> BehaviorStatus:
        self._set_ui_progress(widget, value)
        return BehaviorStatus.SUCCESS

    def _tick_set_ui_visible(self, node_id: str, widget: str, visible: bool, dt: float) -> BehaviorStatus:
        self._set_ui_visible(widget, visible)
        return BehaviorStatus.SUCCESS

    def _tick_decrement_ui_value(self, node_id: str, widget: str, amount: float, dt: float) -> BehaviorStatus:
        self._decrement_ui_value(widget, amount)
        return BehaviorStatus.SUCCESS

    def _tick_increment_ui_value(self, node_id: str, widget: str, amount: float, dt: float) -> BehaviorStatus:
        self._increment_ui_value(widget, amount)
        return BehaviorStatus.SUCCESS

    def _find_ui_widget(self, widget_name: str) -> Any:
        """Procura um widget de UI por nome na cena. Tenta múltiplas estratégias:
        1. Se game_object tem método get_ui_widget, usa-o
        2. Procura em objetos filhos por widget_name ou name
        """
        if not widget_name:
            return None

        # Estratégia 1: método customizado no game_object
        if self.game_object and hasattr(self.game_object, "get_ui_widget"):
            widget = self.game_object.get_ui_widget(widget_name)
            if widget is not None:
                return widget

        # Estratégia 2: procura em objetos filhos por widget_name ou name
        if self.game_object and hasattr(self.game_object, "children"):
            for child in self.game_object.children:
                # Verifica widget_name (padrão para UI Builder)
                if getattr(child, "widget_name", None) == widget_name:
                    return child
                # Fallback: verifica atributo 'name'
                if getattr(child, "name", None) == widget_name:
                    return child

        return None

    def _set_ui_text(self, widget: str, text: str) -> None:
        """Seta texto de UI. Procura widget por nome e atualiza seu texto."""
        widget_obj = self._find_ui_widget(widget)
        if widget_obj is None:
            self._emit_event("ui_action_failed", action="set_text", widget=widget, reason="widget_not_found")
            return

        try:
            if hasattr(widget_obj, "text"):
                widget_obj.text = str(text)
            elif hasattr(widget_obj, "set_text") and callable(widget_obj.set_text):
                widget_obj.set_text(str(text))
            else:
                self._emit_event("ui_action_failed", action="set_text", widget=widget, reason="no_text_property")
                return

            self._emit_event("ui_action_done", action="set_text", widget=widget, value=text)
        except Exception as e:
            self._emit_event("ui_action_failed", action="set_text", widget=widget, error=str(e))

    def _set_ui_progress(self, widget: str, value: float) -> None:
        """Seta valor de barra de progresso de UI."""
        widget_obj = self._find_ui_widget(widget)
        if widget_obj is None:
            self._emit_event("ui_action_failed", action="set_progress", widget=widget, reason="widget_not_found")
            return

        try:
            value = max(0.0, float(value))
            if hasattr(widget_obj, "value"):
                widget_obj.value = value
            elif hasattr(widget_obj, "set_value") and callable(widget_obj.set_value):
                widget_obj.set_value(value)
            else:
                self._emit_event("ui_action_failed", action="set_progress", widget=widget, reason="no_value_property")
                return

            self._emit_event("ui_action_done", action="set_progress", widget=widget, value=value)
        except Exception as e:
            self._emit_event("ui_action_failed", action="set_progress", widget=widget, error=str(e))

    def _set_ui_visible(self, widget: str, visible: bool) -> None:
        """Seta visibilidade de um widget de UI."""
        widget_obj = self._find_ui_widget(widget)
        if widget_obj is None:
            self._emit_event("ui_action_failed", action="set_visible", widget=widget, reason="widget_not_found")
            return

        try:
            if hasattr(widget_obj, "visible"):
                widget_obj.visible = bool(visible)
            elif hasattr(widget_obj, "set_visible") and callable(widget_obj.set_visible):
                widget_obj.set_visible(bool(visible))
            elif hasattr(widget_obj, "enabled"):
                widget_obj.enabled = bool(visible)
            else:
                self._emit_event("ui_action_failed", action="set_visible", widget=widget, reason="no_visibility_property")
                return

            self._emit_event("ui_action_done", action="set_visible", widget=widget, visible=visible)
        except Exception as e:
            self._emit_event("ui_action_failed", action="set_visible", widget=widget, error=str(e))

    def _decrement_ui_value(self, widget: str, amount: float) -> None:
        """Decrementa valor numérico de um widget de UI."""
        widget_obj = self._find_ui_widget(widget)
        if widget_obj is None:
            self._emit_event("ui_action_failed", action="decrement", widget=widget, reason="widget_not_found")
            return

        try:
            amount = float(amount)

            # Tenta atualizar texto (para UILabel com números)
            if hasattr(widget_obj, "text"):
                try:
                    current = float(str(widget_obj.text))
                    new_value = current - amount
                    widget_obj.text = str(int(new_value) if new_value == int(new_value) else new_value)
                except (ValueError, TypeError):
                    self._emit_event("ui_action_failed", action="decrement", widget=widget, reason="text_not_numeric")
                    return
            # Tenta atualizar value (para ProgressBar)
            elif hasattr(widget_obj, "value"):
                current = float(widget_obj.value)
                new_value = current - amount
                if hasattr(widget_obj, "set_value") and callable(widget_obj.set_value):
                    widget_obj.set_value(new_value)
                else:
                    widget_obj.value = new_value
            else:
                self._emit_event("ui_action_failed", action="decrement", widget=widget, reason="no_numeric_property")
                return

            self._emit_event("ui_action_done", action="decrement", widget=widget, amount=amount)
        except Exception as e:
            self._emit_event("ui_action_failed", action="decrement", widget=widget, error=str(e))

    def _increment_ui_value(self, widget: str, amount: float) -> None:
        """Incrementa valor numérico de um widget de UI."""
        widget_obj = self._find_ui_widget(widget)
        if widget_obj is None:
            self._emit_event("ui_action_failed", action="increment", widget=widget, reason="widget_not_found")
            return

        try:
            amount = float(amount)

            # Tenta atualizar texto (para UILabel com números)
            if hasattr(widget_obj, "text"):
                try:
                    current = float(str(widget_obj.text))
                    new_value = current + amount
                    widget_obj.text = str(int(new_value) if new_value == int(new_value) else new_value)
                except (ValueError, TypeError):
                    self._emit_event("ui_action_failed", action="increment", widget=widget, reason="text_not_numeric")
                    return
            # Tenta atualizar value (para ProgressBar)
            elif hasattr(widget_obj, "value"):
                current = float(widget_obj.value)
                new_value = current + amount
                if hasattr(widget_obj, "set_value") and callable(widget_obj.set_value):
                    widget_obj.set_value(new_value)
                else:
                    widget_obj.value = new_value
            else:
                self._emit_event("ui_action_failed", action="increment", widget=widget, reason="no_numeric_property")
                return

            self._emit_event("ui_action_done", action="increment", widget=widget, amount=amount)
        except Exception as e:
            self._emit_event("ui_action_failed", action="increment", widget=widget, error=str(e))

    def _play_animation(self, obj: Any, animation: str) -> None:
        """Toca uma animação. SOBRESCREVA ISSO."""
        pass

    def _emit_event(self, event_type: str, **kwargs: Any) -> None:
        """Emite um evento para debug/logging."""
        self._events.append({"type": event_type, **kwargs})

    @staticmethod
    def _distance(pos_a: tuple[float, float], pos_b: tuple[float, float]) -> float:
        """Calcula distância euclidiana."""
        dx = pos_a[0] - pos_b[0]
        dy = pos_a[1] - pos_b[1]
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _parse_vector2(value: Any) -> tuple[float, float]:
        """Parse um vetor 2D de várias formas."""
        if isinstance(value, (tuple, list)) and len(value) >= 2:
            return (float(value[0]), float(value[1]))
        if isinstance(value, str):
            parts = value.split(",")
            if len(parts) >= 2:
                return (float(parts[0]), float(parts[1]))
        return (0.0, 0.0)
