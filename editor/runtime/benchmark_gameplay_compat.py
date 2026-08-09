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
    _move_enemies(objects, player, dt)


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


def _set_ui_text(objects: dict[str, dict[str, Any]], widget_name: str, text: str) -> None:
    for obj in objects.values():
        ui = obj.get("ui")
        if isinstance(ui, dict) and obj.get("name") == widget_name:
            ui["text"] = text
            return
    # The asset UI renderer also consumes queued logic events, so attach a
    # small event to the HUD carrier when the widget is not represented as a
    # scene object.
    hud = objects.get("HUD")
    if isinstance(hud, dict):
        hud.setdefault("logic_events", []).append({
            "command": "set_ui_text",
            "value": {"object": widget_name, "text": text},
        })
