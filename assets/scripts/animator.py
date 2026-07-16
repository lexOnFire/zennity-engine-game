"""Exemplo simples de contador de quadros de animação."""

# CONFIGURAÇÃO — altere somente estes valores.
FPS_DA_ANIMACAO = 8.0
TOTAL_DE_QUADROS = 4


def on_start(game):
    game.state["quadro"] = 0
    game.state["tempo"] = 0.0


def on_update(game, dt):
    game.state["tempo"] += dt
    tempo_por_quadro = 1.0 / FPS_DA_ANIMACAO

    if game.state["tempo"] >= tempo_por_quadro:
        game.state["tempo"] = 0.0
        game.state["quadro"] = (game.state["quadro"] + 1) % TOTAL_DE_QUADROS
