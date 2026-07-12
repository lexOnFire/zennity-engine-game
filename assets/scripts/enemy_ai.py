"""Inimigo que segue o Player."""

# CONFIGURAÇÃO — altere somente estes valores.
VELOCIDADE = 80.0
DISTANCIA_PARA_PARAR = 40.0
ALVO = "Player"


def on_update(game, dt):
    """A engine chama esta função em todos os frames."""
    player = game.find(ALVO)
    if player is None:
        return

    distancia = game.distance_to(player)
    if distancia <= DISTANCIA_PARA_PARAR:
        return

    passo = min(VELOCIDADE * dt, distancia)
    game.move(
        (player.x - game.x) / distancia * passo,
        (player.y - game.y) / distancia * passo,
    )
