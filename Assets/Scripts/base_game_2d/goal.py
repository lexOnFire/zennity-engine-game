"""Portal final. O Player só vence depois de coletar todas as moedas."""


def on_trigger(game, other):
    if other.tag.lower() == "player":
        other.send("finish")

