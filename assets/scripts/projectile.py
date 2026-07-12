"""Projétil que se move para a direita e desaparece."""

# CONFIGURAÇÃO — altere somente estes valores.
VELOCIDADE = 400.0
TEMPO_DE_VIDA = 2.0


def on_start(game):
    game.state["tempo"] = 0.0


def on_update(game, dt):
    game.move(VELOCIDADE * dt)
    game.state["tempo"] += dt

    if game.state["tempo"] >= TEMPO_DE_VIDA:
        game.destroy()
