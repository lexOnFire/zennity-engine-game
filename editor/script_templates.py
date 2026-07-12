"""Modelos e validação dos scripts usados pela viewport isolada."""
from __future__ import annotations

import ast
from pathlib import Path


REQUIRED_UPDATE_HOOKS = {"on_update", "isolated_update", "update"}


def build_isolated_script_template(script_name: str) -> str:
    safe_name = script_name.removesuffix(".py") or "NewScript"
    return f'''"""{safe_name} — script simples do Zennity."""

CONFIG = {{"speed": 200.0, "jump_force": 420.0}}


def on_update(game, dt):
    """Coloque aqui o que o objeto faz durante o Play."""
    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)

    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])


# Opcional: receba comandos enviados por outros scripts/sistemas.
def on_instruction(game, instruction):
    if instruction.get("command") == "teleport":
        game.x = float(instruction.get("x", game.x))
        game.y = float(instruction.get("y", game.y))
'''


def inspect_script_contract(path: str | Path) -> tuple[bool, str]:
    script_path = Path(path)
    try:
        tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        return False, str(exc)
    hooks = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not hooks.intersection(REQUIRED_UPDATE_HOOKS):
        return False, "defina on_update(game, dt), isolated_update(...) ou update(obj, dt)"
    return True, ""
