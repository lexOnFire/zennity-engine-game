"""Temporizador simples."""

# CONFIGURAÇÃO — altere somente estes valores.
DURACAO = 1.0
REPETIR = False


def on_start(game):
    """A engine chama esta função uma vez ao apertar Play."""
    game.state["tempo"] = 0.0
    game.state["terminou"] = False


def on_update(game, dt):
    """Conta o tempo e marca 'terminou' quando alcançar a duração."""
    if game.state["terminou"] and not REPETIR:
        return

    game.state["tempo"] += dt
    if game.state["tempo"] >= DURACAO:
        game.state["terminou"] = True
        game.log("Tempo concluído")
        if REPETIR:
            game.state["tempo"] = 0.0
