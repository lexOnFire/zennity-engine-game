"""Nós de animação para Logic Graph - Animate Value, Tweens, Lerp 100% visual."""
from __future__ import annotations

import math
import time
from typing import Any, Mapping
from ..registry import registry


@registry.register_executor('animate_value')
def execute_animate_value(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Anima um valor de A para B com duração e easing."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        from_value = float(properties.get("from_value", 0.0))
        to_value = float(properties.get("to_value", 100.0))
        duration = float(properties.get("duration", 1.0))
        easing = str(properties.get("easing", "linear")).lower()
        target_name = str(properties.get("target", ""))
        property_name = str(properties.get("property", "x"))

        # Inicializar animação
        start_time = time.time()
        if not hasattr(runtime, "_animations"):
            runtime._animations = {}

        anim_key = f"{node_id}_animate"
        runtime._animations[anim_key] = {
            "start_time": start_time,
            "from": from_value,
            "to": to_value,
            "duration": duration,
            "easing": easing,
            "target": target_name,
            "property": property_name,
            "finished": False
        }

        # Encontrar target
        if target_name and hasattr(game, "find_object"):
            target = game.find_object(target_name)
            if target:
                elapsed = time.time() - start_time
                progress = min(1.0, elapsed / duration) if duration > 0 else 1.0

                # Aplicar easing
                if easing == "ease_in_quad":
                    progress = progress * progress
                elif easing == "ease_out_quad":
                    progress = 1 - (1 - progress) ** 2
                elif easing == "ease_in_out_quad":
                    progress = 2 * progress ** 2 if progress < 0.5 else -1 + (4 - 2 * progress) * progress
                elif easing == "ease_in_cubic":
                    progress = progress ** 3
                elif easing == "ease_out_cubic":
                    progress = 1 - (1 - progress) ** 3
                elif easing == "ease_in_out_cubic":
                    progress = 4 * progress ** 3 if progress < 0.5 else 1 - (-2 * progress + 2) ** 3 / 2
                # linear é o padrão

                # Interpolar valor
                current_value = from_value + (to_value - from_value) * progress

                # Aplicar ao target
                if hasattr(target, property_name):
                    setattr(target, property_name, current_value)

                # Guardar valor interpolado
                runtime._store(node_id, "value", current_value)
                runtime._store(node_id, "progress", progress)

                if progress >= 1.0:
                    runtime._animations[anim_key]["finished"] = True
                    return ["finished"]
                else:
                    return ["animating"]

        return ["failure"]
    except Exception as e:
        print(f"Erro em animate_value: {e}")
        return ["failure"]


@registry.register_executor('wait_until_condition')
def execute_wait_until_condition(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    """Aguarda até uma condição ser verdadeira com timeout."""
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}

    try:
        condition_type = str(properties.get("condition_type", "variable_equals")).lower()
        timeout = float(properties.get("timeout", 30.0))
        target_name = str(properties.get("target", ""))
        property_name = str(properties.get("property", ""))
        expected_value = properties.get("expected_value", "")
        operator = str(properties.get("operator", "==")).lower()

        # Inicializar timer se não existe
        start_time_key = f"{node_id}_wait_start"
        if not hasattr(runtime, "_wait_timers"):
            runtime._wait_timers = {}

        if start_time_key not in runtime._wait_timers:
            runtime._wait_timers[start_time_key] = time.time()

        start_time = runtime._wait_timers[start_time_key]
        elapsed = time.time() - start_time

        # Verificar timeout
        if elapsed > timeout:
            del runtime._wait_timers[start_time_key]
            return ["timeout"]

        # Verificar condição
        condition_met = False

        if condition_type == "variable_equals":
            var_name = str(properties.get("variable_name", ""))
            current = runtime.blackboard.get("object", var_name, runtime.object_key)
            if current == expected_value:
                condition_met = True

        elif condition_type == "property_greater":
            if target_name and hasattr(game, "find_object"):
                target = game.find_object(target_name)
                if target and hasattr(target, property_name):
                    current = float(getattr(target, property_name, 0))
                    threshold = float(expected_value)
                    if current > threshold:
                        condition_met = True

        elif condition_type == "property_less":
            if target_name and hasattr(game, "find_object"):
                target = game.find_object(target_name)
                if target and hasattr(target, property_name):
                    current = float(getattr(target, property_name, 0))
                    threshold = float(expected_value)
                    if current < threshold:
                        condition_met = True

        if condition_met:
            del runtime._wait_timers[start_time_key]
            runtime._store(node_id, "elapsed_time", elapsed)
            return ["success"]
        else:
            return ["waiting"]

    except Exception as e:
        print(f"Erro em wait_until_condition: {e}")
        return ["failure"]
