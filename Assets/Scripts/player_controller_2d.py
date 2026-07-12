"""Player Controller 2D para a viewport isolada do Zennity."""

CONFIG = {"speed": 240.0, "jump_force": 420.0, "enabled": True}


def isolated_start(obj):
    obj["_jump_was_down"] = False


def isolated_update(obj, input_state, dt):
    if not CONFIG["enabled"]:
        return
    direction = int(input_state["right"]) - int(input_state["left"])
    obj["x"] += direction * CONFIG["speed"] * dt

    jump_down = bool(input_state["jump"])
    if jump_down and not obj.get("_jump_was_down", False):
        obj["_jump_requested"] = True
        obj["_jump_force"] = CONFIG["jump_force"]
    obj["_jump_was_down"] = jump_down


def isolated_on_instruction(obj, instruction):
    command = str(instruction.get("command", ""))
    value = instruction.get("value")
    if command == "set_enabled":
        CONFIG["enabled"] = bool(value)
    elif command == "set_speed":
        CONFIG["speed"] = float(value)
    elif command == "jump":
        obj["_jump_requested"] = True
        obj["_jump_force"] = float(value or CONFIG["jump_force"])


def isolated_stop(obj):
    obj.pop("_jump_was_down", None)
    obj.pop("_jump_requested", None)
    obj.pop("_jump_force", None)
