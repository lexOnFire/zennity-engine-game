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
    _face_player_movement(player)
    _move_enemies(objects, player, dt)
    _damage_player_on_enemy_contact(objects, player, dt)
    _update_game_over(objects, player)
    _update_guard_dialogue(objects, player)


def _rects_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        abs(float(a.get("x", 0.0)) - float(b.get("x", 0.0))) * 2
        < float(a.get("w", 1.0)) + float(b.get("w", 1.0))
        and abs(float(a.get("y", 0.0)) - float(b.get("y", 0.0))) * 2
        < float(a.get("h", 1.0)) + float(b.get("h", 1.0))
    )


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
    guard = objects.get("Guard")
    if not isinstance(guard, dict) or not guard.get("active", True):
        return
    distance = math.hypot(
        float(player.get("x", 0.0)) - float(guard.get("x", 0.0)),
        float(player.get("y", 0.0)) - float(guard.get("y", 0.0)),
    )
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
    if not isinstance(input_state, dict):
        return
    if input_state.get("left") and not input_state.get("right"):
        player["flip_x"] = True
        player["facing_x"] = -1
        player.setdefault("variables", {})["facing_x"] = -1
    elif input_state.get("right") and not input_state.get("left"):
        player["flip_x"] = False
        player["facing_x"] = 1
        player.setdefault("variables", {})["facing_x"] = 1


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
