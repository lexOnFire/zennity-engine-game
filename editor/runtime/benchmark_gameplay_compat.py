"""Small runtime compatibility layer for the bundled benchmark scenes.

The benchmark assets still contain a few dataflow-style generic graphs while
the current Play Mode runtime executes flow-based Logic Graphs.  This module
keeps the shipped benchmark playable until those visual graphs are fully
rewired in the canonical editor.
"""
from __future__ import annotations

import math
from typing import Any


def update_benchmark_gameplay(objects: dict[str, dict[str, Any]], dt: float) -> None:
    player = objects.get("Player")
    if not isinstance(player, dict) or not player.get("active", True):
        return
    _collect_coins(objects, player)
    _collect_key(objects, player)
    _face_player_movement(player)
    _move_enemies(objects, player, dt)
    _damage_player_on_enemy_contact(objects, player, dt)
    _player_attack_enemies_and_boss(objects, player, dt)
    _update_game_over(objects, player)
    _update_guard_dialogue(objects, player)
    _update_door_transition(objects, player)


def _coord(obj: dict[str, Any], key: str, fallback: float) -> float:
    if key in obj:
        try:
            return float(obj.get(key, fallback))
        except (TypeError, ValueError):
            return fallback
    transform = obj.get("transform")
    if isinstance(transform, dict):
        if key in {"x", "y"}:
            position = transform.get("position")
            if isinstance(position, (list, tuple)) and len(position) >= 2:
                try:
                    return float(position[0 if key == "x" else 1])
                except (TypeError, ValueError):
                    return fallback
        if key in {"w", "h"}:
            scale = transform.get("scale")
            if isinstance(scale, (list, tuple)) and len(scale) >= 2:
                try:
                    return float(scale[0 if key == "w" else 1])
                except (TypeError, ValueError):
                    return fallback
    return fallback


def _rects_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        abs(_coord(a, "x", 0.0) - _coord(b, "x", 0.0)) * 2
        < _coord(a, "w", 1.0) + _coord(b, "w", 1.0)
        and abs(_coord(a, "y", 0.0) - _coord(b, "y", 0.0)) * 2
        < _coord(a, "h", 1.0) + _coord(b, "h", 1.0)
    )


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(_coord(a, "x", 0.0) - _coord(b, "x", 0.0), _coord(a, "y", 0.0) - _coord(b, "y", 0.0))


def _matches(obj: dict[str, Any], name: str, tag: str = "") -> bool:
    obj_name = str(obj.get("name", "")).casefold()
    obj_tag = str(obj.get("tag", "")).casefold()
    prefab = str(obj.get("prefab", obj.get("prefab_path", ""))).casefold()
    wanted_name = name.casefold()
    wanted_tag = tag.casefold() if tag else wanted_name
    return (
        obj_name == wanted_name
        or obj_name.startswith(f"{wanted_name} ")
        or obj_name.startswith(f"{wanted_name}_")
        or obj_tag == wanted_tag
        or f"/{wanted_name}.zprfb" in prefab.replace("\\", "/")
    )


def _first_matching(objects: dict[str, dict[str, Any]], name: str, tag: str = "") -> dict[str, Any] | None:
    for obj in objects.values():
        if isinstance(obj, dict) and obj.get("active", True) and _matches(obj, name, tag):
            return obj
    return None


def _touches(a: dict[str, Any], b: dict[str, Any], radius: float) -> bool:
    return _rects_overlap(a, b) or _distance(a, b) <= radius


def _collect_coins(objects: dict[str, dict[str, Any]], player: dict[str, Any]) -> None:
    state = player.setdefault("variables", {})
    for name, obj in list(objects.items()):
        if not name.startswith("Coin") or not obj.get("active", True):
            continue
        if not _rects_overlap(player, obj):
            continue
        obj["active"] = False
        obj["destroyed"] = True
        state["coins"] = int(state.get("coins", 0)) + 1
        _set_ui_text(objects, "CoinsLabel", f"Coins: {state['coins']}")


def _collect_key(objects: dict[str, dict[str, Any]], player: dict[str, Any]) -> None:
    key = _first_matching(objects, "Key", "Key")
    if not isinstance(key, dict) or not key.get("active", True):
        return
    if not _touches(player, key, 56.0):
        return
    key["active"] = False
    key["destroyed"] = True
    state = player.setdefault("variables", {})
    state["has_key"] = True
    state["keys"] = 1
    _set_ui_text(objects, "KeyLabel", "Key: Yes")


def _move_enemies(objects: dict[str, dict[str, Any]], player: dict[str, Any], dt: float) -> None:
    px, py = float(player.get("x", 0.0)), float(player.get("y", 0.0))
    for name, obj in objects.items():
        if not obj.get("active", True):
            continue
        is_enemy = name.startswith("Enemy")
        is_boss = name == "Boss"
        if not (is_enemy or is_boss):
            continue
        dx = px - float(obj.get("x", 0.0))
        dy = py - float(obj.get("y", 0.0))
        distance = math.hypot(dx, dy)
        detection = float((obj.get("variables") or {}).get("detection_range", 900 if is_boss else 650))
        stop = float((obj.get("variables") or {}).get("attack_range", 80 if is_boss else 48))
        if distance <= stop or distance > detection or distance <= 0.001:
            continue
        speed = float((obj.get("variables") or {}).get("move_speed", 95 if is_boss else 120))
        obj["x"] = float(obj.get("x", 0.0)) + (dx / distance) * speed * dt
        obj["y"] = float(obj.get("y", 0.0)) + (dy / distance) * speed * dt
        obj.setdefault("_logic_motion_axes", set()).update({"x", "y"})


def _damage_player_on_enemy_contact(
    objects: dict[str, dict[str, Any]],
    player: dict[str, Any],
    dt: float,
) -> None:
    state = player.setdefault("variables", {})
    state["health"] = int(state.get("health", 100))
    runtime = player.setdefault("_benchmark_state", {})
    cooldown = max(0.0, float(runtime.get("damage_cooldown", 0.0)) - dt)
    runtime["damage_cooldown"] = cooldown
    if cooldown > 0.0:
        return
    for name, obj in objects.items():
        if not obj.get("active", True) or not (name.startswith("Enemy") or name == "Boss"):
            continue
        if not _rects_overlap(player, obj):
            continue
        damage = 20 if name == "Boss" else 10
        state["health"] = max(0, int(state["health"]) - damage)
        runtime["damage_cooldown"] = 0.65
        _set_ui_text(objects, "HealthLabel", f"Health: {state['health']}")
        _set_ui_progress(objects, "HealthBar", state["health"], 100)
        break


def _update_game_over(objects: dict[str, dict[str, Any]], player: dict[str, Any]) -> None:
    state = player.setdefault("variables", {})
    if int(state.get("health", 100)) > 0:
        return
    runtime = player.setdefault("_benchmark_state", {})
    if runtime.get("game_over_requested"):
        return
    runtime["game_over_requested"] = True
    _set_hud(objects, "game_over", "GAME OVER", "center")
    _set_hud(objects, "game_over_hint", "Voltando ao menu...", "bottom-center")
    player.setdefault("logic_events", []).append({
        "command": "load_scene",
        "value": {"path": "Assets/Scenes/GameOver.zscene"},
    })


def _set_ui_text(objects: dict[str, dict[str, Any]], widget_name: str, text: str) -> None:
    _apply_widget_override(objects, widget_name, {"text": text})
    for obj in objects.values():
        ui = obj.get("ui")
        if isinstance(ui, dict) and obj.get("name") == widget_name:
            ui["text"] = text
            return
    carrier = _event_carrier(objects)
    if isinstance(carrier, dict):
        carrier.setdefault("logic_events", []).append({
            "command": "set_ui_text",
            "value": {"object": widget_name, "text": text},
        })


def _set_ui_progress(
    objects: dict[str, dict[str, Any]],
    widget_name: str,
    value: float,
    maximum: float,
) -> None:
    _apply_widget_override(objects, widget_name, {"value": float(value), "max_value": float(maximum)})
    carrier = _event_carrier(objects)
    if isinstance(carrier, dict):
        carrier.setdefault("logic_events", []).append({
            "command": "set_ui_progress",
            "value": {"object": widget_name, "value": float(value), "max_value": float(maximum)},
        })


def _update_guard_dialogue(objects: dict[str, dict[str, Any]], player: dict[str, Any]) -> None:
    guard = _first_matching(objects, "Guard", "NPC")
    if not isinstance(guard, dict) or not guard.get("active", True):
        return
    distance = _distance(player, guard)
    in_range = distance <= 120.0
    player_state = player.setdefault("_benchmark_state", {})
    pressed = bool(player.get("_input", {}).get("interact", False))
    if not in_range:
        _set_hud(objects, "dialogue_hint", "")
        player_state["dialogue_active"] = False
        return
    _set_hud(objects, "dialogue_hint", "Pressione E para falar com o Guard", "bottom-center")
    if pressed:
        player_state["dialogue_active"] = True
        player.setdefault("variables", {})["talked_to_guard"] = True
        text = (
            "Guard: The gate is locked. You must find the key to pass."
            if not bool(player.get("variables", {}).get("has_key", False))
            else "Guard: Excellent! You found the key. You may pass."
        )
        _set_hud(objects, "dialogue", text, "bottom-center")
        _set_ui_text(objects, "DialogueLabel", text)
        player.setdefault("logic_events", []).append({
            "command": "start_dialogue",
            "value": {"speaker": "Guard", "text": text},
        })


def _update_door_transition(objects: dict[str, dict[str, Any]], player: dict[str, Any]) -> None:
    door = _first_matching(objects, "Door", "Door") or _first_matching(objects, "LevelExit", "Door")
    if not isinstance(door, dict) or not door.get("active", True):
        return
    state = player.setdefault("variables", {})
    has_key = bool(state.get("has_key", False))
    talked = bool(state.get("talked_to_guard", False))
    near_door = _touches(player, door, 72.0)
    runtime = player.setdefault("_benchmark_state", {})
    if not near_door:
        _set_hud(objects, "door_hint", "")
        return
    if not has_key:
        _set_hud(objects, "door_hint", "Porta trancada: encontre a chave.", "bottom-center")
        return
    if not talked:
        _set_hud(objects, "door_hint", "Fale com o Guard antes de entrar.", "bottom-center")
        return
    _set_hud(objects, "door_hint", "Porta aberta! Indo para Level 2...", "bottom-center")
    if runtime.get("level2_requested"):
        return
    runtime["level2_requested"] = True
    player.setdefault("logic_events", []).append({
        "command": "load_scene",
        "value": {"path": "Assets/Scenes/Level2.zscene"},
    })


def _set_hud(
    objects: dict[str, dict[str, Any]],
    key: str,
    text: str,
    position: str = "top-left",
) -> None:
    carrier = _event_carrier(objects)
    if not isinstance(carrier, dict):
        return
    if not text:
        carrier.setdefault("logic_events", []).append({"command": "remove_hud", "value": key})
        return
    carrier.setdefault("logic_events", []).append({
        "command": "set_hud",
        "value": {
            "key": key,
            "text": text,
            "position": position,
            "font_size": 20,
            "color": (255, 255, 255),
        },
    })


def _face_player_movement(player: dict[str, Any]) -> None:
    input_state = player.get("_input")
    runtime = player.setdefault("_benchmark_state", {})
    current_x = _coord(player, "x", 0.0)
    current_y = _coord(player, "y", 0.0)
    previous_x = runtime.get("last_player_x")
    previous_y = runtime.get("last_player_y")
    dx = 0.0 if previous_x is None else current_x - float(previous_x)
    dy = 0.0 if previous_y is None else current_y - float(previous_y)
    runtime["last_player_x"] = current_x
    runtime["last_player_y"] = current_y

    left = bool(isinstance(input_state, dict) and input_state.get("left")) or dx < -0.01
    right = bool(isinstance(input_state, dict) and input_state.get("right")) or dx > 0.01
    up = bool(isinstance(input_state, dict) and input_state.get("up")) or dy < -0.01
    down = bool(isinstance(input_state, dict) and input_state.get("down")) or dy > 0.01

    if left and not right:
        player["flip_x"] = True
        player["facing_x"] = -1
        player["rotation"] = 0.0
        player.setdefault("variables", {})["facing_x"] = -1
    elif right and not left:
        player["flip_x"] = False
        player["facing_x"] = 1
        player["rotation"] = 0.0
        player.setdefault("variables", {})["facing_x"] = 1
    elif up and not down:
        player["facing_y"] = -1
        player["rotation"] = 0.0
        player.setdefault("variables", {})["facing_y"] = -1
    elif down and not up:
        player["facing_y"] = 1
        player["rotation"] = 0.0
        player.setdefault("variables", {})["facing_y"] = 1


def _apply_widget_override(
    objects: dict[str, dict[str, Any]],
    widget_name: str,
    values: dict[str, Any],
) -> None:
    for obj in objects.values():
        ui = obj.get("ui")
        if isinstance(ui, dict) and ui.get("type") == "canvas":
            ui.setdefault("_widget_overrides", {}).setdefault(widget_name, {}).update(values)
        components = obj.get("components")
        items = components.get("items", []) if isinstance(components, dict) else []
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("type", "")).lower() not in {"canvas", "uicanvas"}:
                continue
            props = item.setdefault("properties", {})
            if isinstance(props, dict):
                props.setdefault("_widget_overrides", {}).setdefault(widget_name, {}).update(values)


def _event_carrier(objects: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    """Return an object whose logic events are processed by Play Mode."""
    player = objects.get("Player")
    if isinstance(player, dict):
        return player
    hud = objects.get("HUD")
    return hud if isinstance(hud, dict) else None


def _player_attack_enemies_and_boss(
    objects: dict[str, dict[str, Any]],
    player: dict[str, Any],
    dt: float,
) -> None:
    has_combat_logic = any(
        "combat" in str(g.get("path", "")).casefold() or "combat" in str(g.get("name", "")).casefold()
        for g in player.get("logic_graphs", [])
    ) or any("combat" in str(asset).casefold() for asset in player.get("logic_assets", []))
    if not has_combat_logic:
        return
    input_state = player.get("_input")
    runtime = player.setdefault("_benchmark_state", {})
    cooldown = max(0.0, float(runtime.get("attack_cooldown", 0.0)) - dt)
    runtime["attack_cooldown"] = cooldown

    is_attacking = input_state is None or bool(
        isinstance(input_state, dict)
        and (input_state.get("attack") or input_state.get("space") or input_state.get("interact") or input_state.get("fire"))
    )

    p_vars = player.setdefault("variables", {})
    attack_damage = float(p_vars.get("attack_damage", 25))
    attack_range = float(p_vars.get("attack_range", 80.0))

    if cooldown <= 0.0:
        targets = [
            obj for name, obj in objects.items()
            if isinstance(obj, dict)
            and obj.get("active", True)
            and (name.startswith("Enemy") or name == "Boss" or str(obj.get("tag", "")).casefold() in {"enemy", "boss"})
            and _touches(player, obj, attack_range)
        ]
        if targets and is_attacking:
            runtime["attack_cooldown"] = 0.4
            for target in targets:
                t_vars = target.setdefault("variables", {})
                current_hp = float(t_vars.get("health", 500.0 if target.get("name") == "Boss" else 60.0))
                max_hp = float(t_vars.get("max_health", 500.0 if target.get("name") == "Boss" else 60.0))
                new_hp = max(0.0, current_hp - attack_damage)
                t_vars["health"] = new_hp

                if target.get("name") == "Boss" or str(target.get("tag", "")).casefold() == "boss":
                    _set_ui_progress(objects, "BossHealthBar", new_hp, max_hp)
                    if new_hp <= 0.0:
                        target["active"] = False
                        target["destroyed"] = True
                        p_vars["boss_defeated"] = True
                        _set_ui_text(objects, "BossNameLabel", "Boss: Defeated")
                        _set_hud(objects, "victory", "VICTORY!", "center")
                        player.setdefault("logic_events", []).append({
                            "command": "load_scene",
                            "value": {"path": "Assets/Scenes/Victory.zscene"},
                        })
                else:
                    if new_hp <= 0.0:
                        target["active"] = False
                        target["destroyed"] = True
