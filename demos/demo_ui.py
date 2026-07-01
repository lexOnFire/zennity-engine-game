"""
demos/demo_ui.py
─────────────────────────────────────────────────────────────
Demo completa do sistema de UI da Zennity Engine.

Demonstra:
  - Label com shadow
  - Button com hover/press animado
  - ProgressBar com smooth + show_text
  - Panel semi-transparente
  - UICanvas + UIManager
  - Menu de pausa (canvas separado, z_order maior)
  - Tela de Game Over

Controles:
  Esc       Abre/fecha o menu de pausa
  H         Reduz HP em 10
  M         Reduz MP em 15
  X         Cura HP (recarrega para max)
  R         Reseta tudo
"""

import sys, os
pygame = None

import pygame
pygame.init()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.ui import (
    UICanvas, UIManager, Panel, Label, Button, ProgressBar, Anchor, Pivot
)

SW, SH = 800, 600

# ── Estado do jogo ──────────────────────────────────────────
hp     = 100.0
max_hp = 100.0
mp     = 60.0
max_mp = 60.0
score  = 0
paused = False
game_over = False

# ── Pygame setup ────────────────────────────────────────────
screen = pygame.display.set_mode((SW, SH))
pygame.display.set_caption("Zennity Engine — UI Demo")
clock  = pygame.time.Clock()

# ────────────────────────────────────────────────────────────
# HUD Canvas  (z_order=0)
# ────────────────────────────────────────────────────────────
ui = UIManager.instance()
hud = UICanvas(name="HUD", z_order=0)

# ── Painel superior esquerdo (HP / MP)
hud_panel = Panel(
    x=10, y=10, width=220, height=90,
    color=(10, 10, 25, 180),
    border_color=(60, 80, 140, 220),
    border_radius=10,
    anchor=Anchor.TOP_LEFT,
)
hud.add_child(hud_panel)

hud_panel.add_child(Label(
    "HP", x=10, y=8, font_size=14,
    color=(240, 80, 80), bold=True,
))
hp_bar = ProgressBar(
    x=35, y=10, width=170, height=16,
    value=hp, max_value=max_hp,
    color_fill=(200, 60, 60),
    color_bg=(50, 20, 20),
    show_text=True, font_size=11,
    smooth=True, smooth_speed=60.0,
)
hud_panel.add_child(hp_bar)

hud_panel.add_child(Label(
    "MP", x=10, y=38, font_size=14,
    color=(80, 140, 240), bold=True,
))
mp_bar = ProgressBar(
    x=35, y=40, width=170, height=16,
    value=mp, max_value=max_mp,
    color_fill=(60, 100, 220),
    color_bg=(20, 25, 55),
    show_text=True, font_size=11,
    smooth=True, smooth_speed=50.0,
)
hud_panel.add_child(mp_bar)

hud_panel.add_child(Label(
    "H: -HP   M: -MP   X: Curar",
    x=10, y=68, font_size=11, color=(160, 160, 180),
))

# ── Score (canto superior direito)
score_label = Label(
    f"Score: {score}",
    x=-10, y=10,
    font_size=22,
    color=(255, 220, 60),
    bold=True,
    shadow=True,
    anchor=Anchor.TOP_RIGHT,
    pivot=Pivot.TOP_RIGHT,
)
hud.add_child(score_label)

# ── Dica inferior central
hud.add_child(Label(
    "Esc: Pausar",
    x=0, y=-12,
    font_size=14,
    color=(160, 160, 180),
    anchor=Anchor.BOTTOM_CENTER,
    pivot=Pivot.BOTTOM_CENTER,
))

ui.add_canvas(hud)

# ────────────────────────────────────────────────────────────
# Pause Canvas  (z_order=10)
# ────────────────────────────────────────────────────────────
pause_canvas = UICanvas(name="Pause", z_order=10, visible=False)

# Overlay escuro
pause_canvas.add_child(Panel(
    x=0, y=0, width=SW, height=SH,
    color=(0, 0, 0, 140),
    border_color=None,
    border_radius=0,
))

# Janela central
pause_panel = Panel(
    x=0, y=0, width=280, height=240,
    color=(15, 18, 40, 230),
    border_color=(80, 100, 200, 230),
    border_radius=14,
    anchor=Anchor.MIDDLE_CENTER,
    pivot=Pivot.MIDDLE_CENTER,
)
pause_canvas.add_child(pause_panel)

pause_panel.add_child(Label(
    "PAUSADO",
    x=0, y=20,
    font_size=26, bold=True,
    color=(200, 200, 255),
    shadow=True,
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
))

def _resume():
    global paused
    paused = False
    pause_canvas.visible = False

def _quit_game():
    pygame.quit()
    sys.exit()

pause_panel.add_child(Button(
    "Continuar",
    x=0, y=80,
    width=200, height=44,
    on_click=_resume,
    color_normal=(50, 80, 160),
    color_hover=(70, 110, 210),
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
    font_size=18,
))

pause_panel.add_child(Button(
    "+ Score (+50)",
    x=0, y=136,
    width=200, height=44,
    on_click=lambda: _add_score(50),
    color_normal=(40, 100, 60),
    color_hover=(55, 140, 80),
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
    font_size=18,
))

pause_panel.add_child(Button(
    "Sair",
    x=0, y=192,
    width=200, height=44,
    on_click=_quit_game,
    color_normal=(120, 40, 40),
    color_hover=(170, 55, 55),
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
    font_size=18,
))

ui.add_canvas(pause_canvas)

# ────────────────────────────────────────────────────────────
# Game Over Canvas  (z_order=20)
# ────────────────────────────────────────────────────────────
gameover_canvas = UICanvas(name="GameOver", z_order=20, visible=False)

gameover_canvas.add_child(Panel(
    x=0, y=0, width=SW, height=SH,
    color=(0, 0, 0, 200),
    border_color=None, border_radius=0,
))

gover_panel = Panel(
    x=0, y=0, width=320, height=200,
    color=(30, 8, 8, 240),
    border_color=(200, 50, 50, 230),
    border_radius=14,
    anchor=Anchor.MIDDLE_CENTER,
    pivot=Pivot.MIDDLE_CENTER,
)
gameover_canvas.add_child(gover_panel)

gover_panel.add_child(Label(
    "GAME OVER",
    x=0, y=20,
    font_size=30, bold=True,
    color=(220, 60, 60),
    shadow=True,
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
))

gover_score_label = Label(
    "Score: 0",
    x=0, y=72,
    font_size=20,
    color=(220, 200, 100),
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
)
gover_panel.add_child(gover_score_label)

def _restart():
    global hp, mp, score, game_over
    hp, mp, score, game_over = max_hp, max_mp, 0, False
    hp_bar.set_value(hp)
    mp_bar.set_value(mp)
    score_label.set_text(f"Score: {score}")
    gameover_canvas.visible = False
    hud.visible = True

gover_panel.add_child(Button(
    "Reiniciar",
    x=0, y=120,
    width=200, height=44,
    on_click=_restart,
    color_normal=(60, 40, 120),
    color_hover=(90, 60, 170),
    anchor=Anchor.TOP_CENTER,
    pivot=Pivot.TOP_CENTER,
    font_size=18,
))

ui.add_canvas(gameover_canvas)


# ── Helpers ─────────────────────────────────────────────────
def _add_score(v: int):
    global score
    score += v
    score_label.set_text(f"Score: {score}")

def _trigger_game_over():
    global game_over
    game_over = True
    hud.visible = False
    gover_score_label.set_text(f"Score: {score}")
    gameover_canvas.visible = True


# ── Fundo procedural ────────────────────────────────────────
def _draw_bg(surface):
    surface.fill((18, 22, 38))
    font = pygame.font.SysFont("monospace", 13)
    lines = [
        "Zennity Engine — Sistema de UI",
        "",
        "H  →  reduz HP em 10",
        "M  →  reduz MP em 15",
        "X  →  cura HP (max)",
        "Esc →  pausa / retoma",
        "R  →  reseta tudo",
    ]
    for i, line in enumerate(lines):
        surf = font.render(line, True, (55, 65, 90))
        surface.blit(surf, (SW//2 - surf.get_width()//2, SH//2 - 80 + i*22))


# ── Loop principal ───────────────────────────────────────────
running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        consumed = ui.handle_event(event, screen)

        if not consumed and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not game_over:
                paused = not paused
                pause_canvas.visible = paused

            elif event.key == pygame.K_h and not paused and not game_over:
                hp = max(0.0, hp - 10)
                hp_bar.set_value(hp)
                score += 5
                score_label.set_text(f"Score: {score}")
                if hp <= 0:
                    _trigger_game_over()

            elif event.key == pygame.K_m and not paused and not game_over:
                mp = max(0.0, mp - 15)
                mp_bar.set_value(mp)

            elif event.key == pygame.K_x and not paused and not game_over:
                hp = max_hp
                hp_bar.set_value(hp)

            elif event.key == pygame.K_r:
                _restart()

    ui.update(dt)

    _draw_bg(screen)
    ui.draw(screen)
    pygame.display.flip()

pygame.quit()
