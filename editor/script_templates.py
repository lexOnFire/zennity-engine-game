"""Modelos e validação dos scripts usados pela viewport isolada."""
from __future__ import annotations

import ast
from pathlib import Path


REQUIRED_UPDATE_HOOKS = {"isolated_update", "update"}


def build_isolated_script_template(script_name: str) -> str:
    safe_name = script_name.removesuffix(".py") or "NewScript"
    return f'''"""{safe_name} — comportamento criado pelo Zennity Editor.

API disponível:
- obj: dicionário do objeto (x, y, w, h, rotation, rigidbody, collider).
- input_state: left, right, up, down e jump.
- dt: tempo do frame em segundos.
- instruction: mensagens enviadas ao script por outros sistemas.
"""

ENABLED = True
CONFIG = {{
    "speed": 200.0,
}}


def isolated_start(obj):
    """Executado uma vez ao entrar no Play."""
    obj.setdefault("script_state", {{}})


def isolated_update(obj, input_state, dt):
    """Executado a cada frame enquanto o jogo não estiver pausado."""
    if not ENABLED:
        return

    # Exemplo de entrada; remova o comentário para movimentar no eixo X.
    # direction = int(input_state["right"]) - int(input_state["left"])
    # obj["x"] += direction * CONFIG["speed"] * dt


def isolated_on_instruction(obj, instruction):
    """Recebe dicts como {{"command": "...", "value": ...}}."""
    command = str(instruction.get("command", ""))
    value = instruction.get("value")

    if command == "set_enabled":
        obj.setdefault("script_state", {{}})["enabled"] = bool(value)
    elif command == "set_speed":
        CONFIG["speed"] = float(value)


def isolated_stop(obj):
    """Executado uma vez ao sair do Play."""
    obj.pop("script_state", None)
'''


def inspect_script_contract(path: str | Path) -> tuple[bool, str]:
    script_path = Path(path)
    try:
        tree = ast.parse(script_path.read_text(encoding="utf-8"), filename=str(script_path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        return False, str(exc)
    hooks = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not hooks.intersection(REQUIRED_UPDATE_HOOKS):
        return False, "defina isolated_update(obj, input_state, dt) ou update(obj, dt)"
    return True, ""
