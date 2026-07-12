"""Sistema simples de vida."""

# CONFIGURAÇÃO — altere somente este valor.
VIDA_MAXIMA = 100


def on_start(game):
    game.state["vida"] = VIDA_MAXIMA


def on_update(game, dt):
    if game.state["vida"] <= 0:
        game.destroy()


def on_instruction(game, instruction):
    """Recebe os comandos 'damage' e 'heal'."""
    comando = instruction.get("command")
    valor = int(instruction.get("value", 0))

    if comando == "damage":
        game.state["vida"] -= valor
    elif comando == "heal":
        game.state["vida"] = min(VIDA_MAXIMA, game.state["vida"] + valor)
