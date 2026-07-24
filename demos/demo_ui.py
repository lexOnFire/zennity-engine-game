"""
demos/demo_ui.py
─────────────────────────────────────────────────────────────
Demo completa do sistema de UI da Zennity Engine.
"""

import sys
import os
import pygame

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine.core import Engine, Scene
from engine.ui import (
    UICanvas, UIManager, Panel, Label, Button, ProgressBar, Anchor, Pivot
)

SW, SH = 800, 600

class UIDemoScene(Scene):
    def start(self):
        # ── Estado do jogo ──
        self.hp = 100.0
        self.max_hp = 100.0
        self.mp = 60.0
        self.max_mp = 60.0
        self.score = 0
        self.paused = False
        self.game_over = False

        # ── Setup do UIManager
        self.ui = UIManager.instance()
        self.ui.clear()  # Limpa canvas antigos

        # ── HUD Canvas (z_order=0) ──
        self.hud = UICanvas(name="HUD", z_order=0)

        # Painel superior esquerdo (HP / MP)
        self.hud_panel = Panel(
            x=10, y=10, width=220, height=90,
            color=(10, 10, 25, 180),
            border_color=(60, 80, 140, 220),
            border_radius=10,
            anchor=Anchor.TOP_LEFT,
        )
        self.hud.add_child(self.hud_panel)

        self.hud_panel.add_child(Label(
            "HP", x=10, y=8, font_size=14,
            color=(240, 80, 80), bold=True,
        ))
        self.hp_bar = ProgressBar(
            x=35, y=10, width=170, height=16,
            value=self.hp, max_value=self.max_hp,
            color_fill=(200, 60, 60),
            color_bg=(50, 20, 20),
            show_text=True, font_size=11,
            smooth=True, smooth_speed=60.0,
        )
        self.hud_panel.add_child(self.hp_bar)

        self.hud_panel.add_child(Label(
            "MP", x=10, y=38, font_size=14,
            color=(80, 140, 240), bold=True,
        ))
        self.mp_bar = ProgressBar(
            x=35, y=40, width=170, height=16,
            value=self.mp, max_value=self.max_mp,
            color_fill=(60, 100, 220),
            color_bg=(20, 25, 55),
            show_text=True, font_size=11,
            smooth=True, smooth_speed=50.0,
        )
        self.hud_panel.add_child(self.mp_bar)

        self.hud_panel.add_child(Label(
            "H: -HP   M: -MP   X: Curar",
            x=10, y=68, font_size=11, color=(160, 160, 180),
        ))

        # Score (canto superior direito)
        self.score_label = Label(
            f"Score: {self.score}",
            x=-10, y=10,
            font_size=22,
            color=(255, 220, 60),
            bold=True,
            shadow=True,
            anchor=Anchor.TOP_RIGHT,
            pivot=Pivot.TOP_RIGHT,
        )
        self.hud.add_child(self.score_label)

        # Dica inferior central
        self.hud.add_child(Label(
            "Esc: Pausar",
            x=0, y=-12,
            font_size=14,
            color=(160, 160, 180),
            anchor=Anchor.BOTTOM_CENTER,
            pivot=Pivot.BOTTOM_CENTER,
        ))

        self.ui.add_canvas(self.hud)

        # ── Pause Canvas (z_order=10) ──
        self.pause_canvas = UICanvas(name="Pause", z_order=10, visible=False)

        # Overlay escuro
        self.pause_canvas.add_child(Panel(
            x=0, y=0, width=SW, height=SH,
            color=(0, 0, 0, 140),
            border_color=None,
            border_radius=0,
        ))

        # Janela central
        self.pause_panel = Panel(
            x=0, y=0, width=280, height=240,
            color=(15, 18, 40, 230),
            border_color=(80, 100, 200, 230),
            border_radius=14,
            anchor=Anchor.MIDDLE_CENTER,
            pivot=Pivot.MIDDLE_CENTER,
        )
        self.pause_canvas.add_child(self.pause_panel)

        self.pause_panel.add_child(Label(
            "PAUSADO",
            x=0, y=20,
            font_size=26, bold=True,
            color=(200, 200, 255),
            shadow=True,
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
        ))

        self.pause_panel.add_child(Button(
            "Continuar",
            x=0, y=80,
            width=200, height=44,
            on_click=self._resume,
            color_normal=(50, 80, 160),
            color_hover=(70, 110, 210),
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
            font_size=18,
        ))

        self.pause_panel.add_child(Button(
            "+ Score (+50)",
            x=0, y=136,
            width=200, height=44,
            on_click=lambda: self._add_score(50),
            color_normal=(40, 100, 60),
            color_hover=(55, 140, 80),
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
            font_size=18,
        ))

        self.pause_panel.add_child(Button(
            "Sair",
            x=0, y=192,
            width=200, height=44,
            on_click=self._quit_game,
            color_normal=(120, 40, 40),
            color_hover=(170, 55, 55),
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
            font_size=18,
        ))

        self.ui.add_canvas(self.pause_canvas)

        # ── Game Over Canvas (z_order=20) ──
        self.gameover_canvas = UICanvas(name="GameOver", z_order=20, visible=False)

        self.gameover_canvas.add_child(Panel(
            x=0, y=0, width=SW, height=SH,
            color=(0, 0, 0, 200),
            border_color=None, border_radius=0,
        ))

        self.gover_panel = Panel(
            x=0, y=0, width=320, height=200,
            color=(30, 8, 8, 240),
            border_color=(200, 50, 50, 230),
            border_radius=14,
            anchor=Anchor.MIDDLE_CENTER,
            pivot=Pivot.MIDDLE_CENTER,
        )
        self.gameover_canvas.add_child(self.gover_panel)

        self.gover_panel.add_child(Label(
            "GAME OVER",
            x=0, y=20,
            font_size=30, bold=True,
            color=(220, 60, 60),
            shadow=True,
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
        ))

        self.gover_score_label = Label(
            "Score: 0",
            x=0, y=72,
            font_size=20,
            color=(220, 200, 100),
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
        )
        self.gover_panel.add_child(self.gover_score_label)

        self.gover_panel.add_child(Button(
            "Reiniciar",
            x=0, y=120,
            width=200, height=44,
            on_click=self._restart,
            color_normal=(60, 40, 120),
            color_hover=(90, 60, 170),
            anchor=Anchor.TOP_CENTER,
            pivot=Pivot.TOP_CENTER,
            font_size=18,
        ))

        self.ui.add_canvas(self.gameover_canvas)

        # Fonte do background
        self.bg_font = pygame.font.SysFont("monospace", 13)

    def _resume(self):
        self.paused = False
        self.pause_canvas.visible = False

    def _quit_game(self):
        pygame.quit()
        sys.exit()

    def _restart(self):
        self.hp, self.mp, self.score, self.game_over = self.max_hp, self.max_mp, 0, False
        self.hp_bar.set_value(self.hp)
        self.mp_bar.set_value(self.mp)
        self.score_label.set_text(f"Score: {self.score}")
        self.gameover_canvas.visible = False
        self.hud.visible = True

    def _add_score(self, v: int):
        self.score += v
        self.score_label.set_text(f"Score: {self.score}")

    def _trigger_game_over(self):
        self.game_over = True
        self.hud.visible = False
        self.gover_score_label.set_text(f"Score: {self.score}")
        self.gameover_canvas.visible = True

    def update(self, dt: float):
        self.ui.update(dt)

    def handle_event(self, event):
        scr = pygame.display.get_surface()
        consumed = self.ui.handle_event(event, scr)

        if not consumed and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not self.game_over:
                self.paused = not self.paused
                self.pause_canvas.visible = self.paused

            elif event.key == pygame.K_h and not self.paused and not self.game_over:
                self.hp = max(0.0, self.hp - 10)
                self.hp_bar.set_value(self.hp)
                self.score += 5
                self.score_label.set_text(f"Score: {self.score}")
                if self.hp <= 0:
                    self._trigger_game_over()

            elif event.key == pygame.K_m and not self.paused and not self.game_over:
                self.mp = max(0.0, self.mp - 15)
                self.mp_bar.set_value(self.mp)

            elif event.key == pygame.K_x and not self.paused and not self.game_over:
                self.hp = self.max_hp
                self.hp_bar.set_value(self.hp)

            elif event.key == pygame.K_r:
                self._restart()

    def draw(self, screen: pygame.Surface):
        # Desenha fundo
        screen.fill((18, 22, 38))
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
            surf = self.bg_font.render(line, True, (55, 65, 90))
            screen.blit(surf, (SW//2 - surf.get_width()//2, SH//2 - 80 + i*22))

        # Desenha a UI no topo
        self.ui.draw(screen)

if __name__ == "__main__":
    pygame.init()
    engine = Engine(width=SW, height=SH, title="Zennity — UI Demo", fps=60)
    engine.run(UIDemoScene())
