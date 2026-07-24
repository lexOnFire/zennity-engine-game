"""Player da demo do Animator Controller.

Controles: A/D para mover, Espaço para pular e S para atacar.
"""

CONFIG = {"speed": 220.0, "jump_force": 440.0}


def on_start(game):
    game.state["last_transition"] = "Inicializando"
    game.set_hud("anim_help", "A/D: mover | ESPAÇO: pular | S: atacar", (190, 205, 230), "bottom-left", 18)
    game.log("Demo Animator iniciada")


def on_update(game, dt):
    direction = game.axis("left", "right")
    game.move(direction * CONFIG["speed"] * dt)
    game.animator.set_float("speed", abs(direction))
    game.animator.set_bool("grounded", game.grounded)

    if game.key_pressed("space"):
        game.jump(CONFIG["jump_force"])
    if game.key_pressed("down"):
        game.animator.trigger("attack")

    game.set_hud("anim_state", f"ESTADO: {game.animator.state}", (112, 255, 163), "top-left", 24)
    game.set_hud(
        "anim_params",
        f"speed={abs(direction):.1f}  grounded={game.grounded}",
        (225, 230, 240), "top-left", 18,
    )
    game.set_hud("anim_transition", game.state.get("last_transition", ""), (255, 201, 94), "top-right", 17)


def on_animation_event(game, event):
    if event == "passo":
        game.play_sound("Assets/Audio/collect-points-190037.mp3")
    elif event == "pulo":
        game.play_sound("Assets/Audio/jump-sound-531048.mp3")
    elif event == "ataque_inicio":
        hitbox = game.find("AttackHitbox")
        if hitbox:
            hitbox.x = game.x + 52.0
            hitbox.y = game.y
            hitbox.active = True
    elif event == "ataque_fim":
        hitbox = game.find("AttackHitbox")
        if hitbox:
            hitbox.active = False


def on_animation_state_enter(game, state):
    game.state["last_transition"] = "Entrou em " + state
    game.log(game.state["last_transition"])


def on_animation_state_exit(game, state):
    game.state["last_transition"] = "Saiu de " + state


def on_stop(game):
    hitbox = game.find("AttackHitbox")
    if hitbox:
        hitbox.active = False
