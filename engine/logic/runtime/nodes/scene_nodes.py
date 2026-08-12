from __future__ import annotations
import math
import random
from typing import Any, Mapping
from ..registry import registry

@registry.register_evaluator('delta_time')
def evaluate_delta_time(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    value = float(dt)
    return value

@registry.register_evaluator('get_tag')
def evaluate_get_tag(runtime, node_id: str, port: str, node: Mapping[str, Any], game: Any, dt: float, branch: set[str]) -> Any:
    node_type = str(node.get('type'))
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    target = runtime._read_target(node_id, game, dt, branch)
    value = str(getattr(target, "tag", "Untagged"))
    return value


@registry.register_executor(('scene.load_scene', 'open_scene', 'load_scene'))
def execute_scene_load_scene(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    inputs = node.get('inputs', {}) if isinstance(node.get('inputs'), Mapping) else {}
    scene_path = str(runtime._read_input(node_id, "scene_path", inputs.get("scene_path", properties.get("scene_path", properties.get("scene", ""))), game, dt, set()))

    if scene_path and hasattr(game, "load_scene"):
        game.load_scene(scene_path)
    elif scene_path and hasattr(game, "open_scene"):
        game.open_scene(scene_path)
    elif scene_path and hasattr(game, "send"):
        game.send("load_scene", {"path": scene_path})
    return ["success", "next"]


@registry.register_executor(('app.quit', 'quit_game', 'exit_game'))
def execute_app_quit(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    if hasattr(game, "quit"):
        game.quit()
    elif hasattr(game, "stop"):
        game.stop()
    return []


@registry.register_executor(('variables.set', 'set_variable'))
def execute_variables_set(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    inputs = node.get('inputs', {}) if isinstance(node.get('inputs'), Mapping) else {}
    name = str(runtime._read_input(node_id, "name", inputs.get("name", properties.get("name", "")), game, dt, set()))
    val = runtime._read_input(node_id, "value", inputs.get("value", properties.get("value", 0)), game, dt, set())
    scope = str(properties.get("scope", inputs.get("scope", "object"))).lower()

    if name:
        if hasattr(runtime, "blackboard") and hasattr(runtime.blackboard, "set"):
            runtime.blackboard.set(scope, name, val, getattr(runtime, "object_key", "default"))
            runtime.variables = runtime.blackboard.values_for_object(getattr(runtime, "object_key", "default"))
        else:
            runtime.variables[name] = val
        if hasattr(game, "set_variable"):
            game.set_variable(name, val)
    # ``done`` was never declared, appears in no asset and is asserted by no
    # test -- it could only ever have been followed by an edge the editor
    # cannot create. ``next`` is the contract, and what all 12 shipping flow
    # edges are wired to.
    return ["next"]


@registry.register_executor(('ui.button_clicked', 'button_clicked', 'on_ui_click'))
def execute_ui_button_clicked(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    node_id = str(node['id'])
    properties = node.get('properties', {}) if isinstance(node.get('properties'), Mapping) else {}
    inputs = node.get('inputs', {}) if isinstance(node.get('inputs'), Mapping) else {}
    expected = str(inputs.get("widget_name", properties.get("widget_name", properties.get("button", "")))).strip().lower()

    payload = runtime.values.get((node_id, "other")) or runtime.values.get((node_id, "payload")) or {}
    clicked_widget = ""
    if isinstance(payload, dict):
        clicked_widget = str(payload.get("widget_name") or payload.get("button") or "").strip().lower()

    if not expected or not clicked_widget or expected == clicked_widget:
        return ["clicked", "next", "exec"]
    return []


# PHASE 9 recovery item 6: the load_game and has_save executors that used to
# live here were the losing half of a split brain, and they won by load order.
# The has_save one did nothing at all -- it returned ["false"] without checking
# for a save -- and the load_game one ignored the declared slot_name property.
# save_load_nodes has the real implementations; only one executor may own an id.


@registry.register_executor(('ui.set_widget_enabled', 'set_ui_enabled'))
def execute_ui_set_widget_enabled(runtime, node: Mapping[str, Any], game: Any, dt: float) -> list[str]:
    return ["next"]

