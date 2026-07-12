"""Player Controller 2D para a viewport isolada do Zennity."""

SPEED = 240.0
JUMP_FORCE = 420.0


def isolated_start(obj):
    obj["_jump_was_down"] = False


def isolated_update(obj, input_state, dt):
    direction = int(input_state["right"]) - int(input_state["left"])
    obj["x"] += direction * SPEED * dt

    jump_down = bool(input_state["jump"])
    if jump_down and not obj.get("_jump_was_down", False):
        obj["_jump_requested"] = True
        obj["_jump_force"] = JUMP_FORCE
    obj["_jump_was_down"] = jump_down


def isolated_stop(obj):
    obj.pop("_jump_was_down", None)
    obj.pop("_jump_requested", None)
    obj.pop("_jump_force", None)
