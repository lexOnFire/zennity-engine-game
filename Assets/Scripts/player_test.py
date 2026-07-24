"""player_test — comportamento criado pelo Zennity Editor.

API disponível:
- obj: dicionário do objeto (x, y, w, h, rotation, rigidbody, collider).
- input_state: left, right, up, down e jump.
- dt: tempo do frame em segundos.
- instruction: mensagens enviadas ao script por outros sistemas.
"""

ENABLED = True
CONFIG = {
    "speed": 200.0,
}


def isolated_start(obj):
    """Executado uma vez ao entrar no Play."""
    obj.setdefault("script_state", {})


def isolated_update(obj, input_state, dt):
    """Executado a cada frame enquanto o jogo não estiver pausado."""
    if not ENABLED:
        return

    # Exemplo de entrada; remova o comentário para movimentar no eixo X.
    # direction = int(input_state["right"]) - int(input_state["left"])
    # obj["x"] += direction * CONFIG["speed"] * dt


def isolated_on_instruction(obj, instruction):
    """Recebe dicts como {"command": "...", "value": ...}."""
    command = str(instruction.get("command", ""))
    value = instruction.get("value")

    if command == "set_enabled":
        obj.setdefault("script_state", {})["enabled"] = bool(value)
    elif command == "set_speed":
        CONFIG["speed"] = float(value)


def isolated_stop(obj):
    """Executado uma vez ao sair do Play."""
    obj.pop("script_state", None)
