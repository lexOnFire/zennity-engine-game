"""
demos/demo_scene_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Demo do SceneManager com transições visuais da Zennity Engine.

Cenas:
  SplashScene  → TitleScene  → GameScene  → GameOverScene
                    ↑                             │
                    └─────────── Restart ─────────┘

Transições:
  Splash → Title    : FadeTransition    (branco)
  Title  → Game     : WipeTransition    (horizontal)
  Game   → GameOver : FadeTransition    (vermelho)
  GameOver → Title  : CrossfadeTransition
  PauseScene (push/pop): SlideTransition (UP/DOWN)

Controles:
  Enter / Space  Avançar / Confirmar
  Esc            Abrir/fechar pausa
  H              Reduzir HP (na GameScene)
  F11            Fullscreen
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame

from engine.core         import Engine, Scene
from engine.scene_manager import SceneManager
from engine.transitions  import (
    FadeTransition, WipeTransition,
    CrossfadeTransition, SlideTransition, SlideDirection,
)
from engine.ui import (
    UICanvas, UIManager, Panel, Label, Button,
    ProgressBar, Anchor, Pivot,
)

SW, SH = 800, 600


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _font(size, bold=False):
    return pygame.font.SysFont("sans", size, bold=bold)

def _center_text(screen, font, text, y, color):
    surf = font.render(text, True, color)
    screen.blit(surf, (SW // 2 - surf.get_width() // 2, y))


# ─── SplashScene ──────────────────────────────────────────────────────────────

class SplashScene(Scene):
    """Tela de splash com logo animado + auto-avanço após 2s."""

    def start(self):
        self._timer  = 0.0
        self._done   = False
        self._font_l = _font(48, bold=True)
        self._font_s = _font(18)
        self._alpha  = 0.0   # fade-in do logo

    def update(self, dt):
        self._timer += dt
        self._alpha  = min(1.0, self._timer / 0.8)  # aparece em 0.8s
        if self._timer >= 2.2 and not self._done:
            self._done = True
            sm = SceneManager.instance()
            sm.load(
                TitleScene(),
                FadeTransition(color=(255, 255, 255),
                               duration_out=0.5, duration_in=0.5),
            )

    def draw(self, screen):
        screen.fill((15, 15, 25))
        # Logo "Z" centralizado
        surf = self._font_l.render("ZENNITY", True, (255, 255, 255))
        surf.set_alpha(int(self._alpha * 255))
        screen.blit(surf, (SW // 2 - surf.get_width() // 2, SH // 2 - 40))
        sub = self._font_s.render("Engine v1.0", True, (120, 120, 140))
        sub.set_alpha(int(self._alpha * 200))
        screen.blit(sub, (SW // 2 - sub.get_width() // 2, SH // 2 + 20))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            if not self._done:
                self._done = True
                SceneManager.instance().load(
                    TitleScene(),
                    FadeTransition(color=(255, 255, 255),
                                   duration_out=0.3, duration_in=0.4),
                )


# ─── TitleScene ───────────────────────────────────────────────────────────────

class TitleScene(Scene):
    """Menu principal com botões de UI."""

    def start(self):
        self._ui = UIManager.instance()
        canvas   = UICanvas(name="Title", z_order=0)

        panel = Panel(
            x=0, y=0, width=360, height=300,
            color=(12, 14, 35, 220),
            border_color=(70, 90, 200, 200),
            border_radius=16,
            anchor=Anchor.MIDDLE_CENTER,
            pivot=Pivot.MIDDLE_CENTER,
        )
        canvas.add_child(panel)

        panel.add_child(Label(
            "ZENNITY ENGINE",
            x=0, y=20, font_size=28, bold=True,
            color=(200, 210, 255), shadow=True,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Label(
            "Demo do SceneManager",
            x=0, y=62, font_size=15,
            color=(140, 150, 200),
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        panel.add_child(Button(
            "▶  Jogar",
            x=0, y=100, width=240, height=48,
            on_click=self._go_game,
            color_normal=(40, 70, 160), color_hover=(60, 100, 210),
            font_size=20,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Button(
            "✕  Sair",
            x=0, y=162, width=240, height=48,
            on_click=lambda: (pygame.quit(), sys.exit()),
            color_normal=(100, 30, 30), color_hover=(150, 45, 45),
            font_size=20,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        panel.add_child(Label(
            "Enter ou click em Jogar",
            x=0, y=228, font_size=13, color=(100, 110, 160),
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        self._ui.add_canvas(canvas)

    def _go_game(self):
        SceneManager.instance().load(
            GameScene(),
            WipeTransition(horizontal=True, duration_out=0.3, duration_in=0.3),
        )

    def update(self, dt):
        self._ui.update(dt)

    def draw(self, screen):
        screen.fill((8, 10, 22))
        # Grade decorativa
        for x in range(0, SW, 40):
            pygame.draw.line(screen, (20, 22, 45), (x, 0), (x, SH))
        for y in range(0, SH, 40):
            pygame.draw.line(screen, (20, 22, 45), (0, y), (SW, y))
        self._ui.draw(screen)

    def handle_event(self, event):
        self._ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._go_game()


# ─── PauseScene ───────────────────────────────────────────────────────────────

class PauseScene(Scene):
    """Menu de pausa — empilhado (push) sobre GameScene."""

    def start(self):
        self._ui = UIManager.instance()
        canvas   = UICanvas(name="Pause", z_order=10)

        # Overlay
        canvas.add_child(Panel(
            x=0, y=0, width=SW, height=SH,
            color=(0, 0, 0, 140), border_color=None, border_radius=0,
        ))

        panel = Panel(
            x=0, y=0, width=300, height=240,
            color=(14, 16, 40, 235),
            border_color=(80, 100, 220, 220),
            border_radius=14,
            anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER,
        )
        canvas.add_child(panel)

        panel.add_child(Label(
            "PAUSADO", x=0, y=18, font_size=26, bold=True,
            color=(180, 190, 255), shadow=True,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Button(
            "Continuar", x=0, y=72, width=220, height=46,
            on_click=self._resume,
            color_normal=(40, 70, 150), color_hover=(60, 100, 210),
            font_size=18,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Button(
            "Menu Principal", x=0, y=130, width=220, height=46,
            on_click=self._to_menu,
            color_normal=(80, 40, 40), color_hover=(120, 55, 55),
            font_size=18,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        panel.add_child(Label(
            "Esc: retomar", x=0, y=192, font_size=13, color=(90, 100, 160),
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        self._ui.add_canvas(canvas)

    def _resume(self):
        SceneManager.instance().pop(
            SlideTransition(SlideDirection.DOWN, duration_in=0.3)
        )

    def _to_menu(self):
        SceneManager.instance().load(
            TitleScene(),
            FadeTransition(duration_out=0.3, duration_in=0.3),
        )

    def update(self, dt):
        self._ui.update(dt)

    def draw(self, screen):
        # PauseScene não limpa a tela — a cena abaixo já foi desenhada
        self._ui.draw(screen)

    def handle_event(self, event):
        self._ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._resume()


# ─── GameScene ────────────────────────────────────────────────────────────────

class GameScene(Scene):
    """Cena de jogo simples com barra de HP e timer."""

    def start(self):
        self._hp     = 100.0
        self._score  = 0
        self._timer  = 0.0
        self._font   = _font(22, bold=True)
        self._font_s = _font(15)

        self._ui   = UIManager.instance()
        canvas     = UICanvas(name="GameHUD", z_order=0)

        # HP bar
        panel = Panel(
            x=10, y=10, width=230, height=55,
            color=(10, 12, 28, 190),
            border_color=(60, 80, 160, 200),
            border_radius=10,
        )
        canvas.add_child(panel)
        panel.add_child(Label(
            "HP", x=10, y=10, font_size=14, color=(240, 80, 80), bold=True
        ))
        self._hp_bar = ProgressBar(
            x=35, y=12, width=178, height=16,
            value=100, max_value=100,
            color_fill=(200, 60, 60), color_bg=(45, 18, 18),
            smooth=True, smooth_speed=60.0, show_text=True, font_size=11,
        )
        panel.add_child(self._hp_bar)
        panel.add_child(Label(
            "H: -10 HP  |  Esc: pausa",
            x=10, y=34, font_size=11, color=(130, 140, 180),
        ))

        # Score
        self._score_lbl = Label(
            "Score: 0", x=-10, y=10, font_size=22, bold=True,
            color=(255, 215, 60), shadow=True,
            anchor=Anchor.TOP_RIGHT, pivot=Pivot.TOP_RIGHT,
        )
        canvas.add_child(self._score_lbl)

        self._ui.add_canvas(canvas)

    def update(self, dt):
        self._timer += dt
        self._score  = int(self._timer * 10)
        self._score_lbl.set_text(f"Score: {self._score}")
        self._ui.update(dt)

    def draw(self, screen):
        # Fundo de jogo
        screen.fill((18, 24, 38))
        for x in range(0, SW, 60):
            pygame.draw.line(screen, (24, 32, 52), (x, 0), (x, SH))
        for y in range(0, SH, 60):
            pygame.draw.line(screen, (24, 32, 52), (0, y), (SW, y))

        # "Player" placeholder
        px, py = SW // 2, SH // 2 + 40
        pygame.draw.rect(screen, (80, 160, 240),
                         (px - 16, py - 24, 32, 48), border_radius=4)
        pygame.draw.ellipse(screen, (80, 160, 240),
                            (px - 10, py - 36, 20, 20))

        cx = SW // 2
        cy = SH - 60
        f = _font(14)
        for i, line in enumerate([
            f"Tempo: {self._timer:.1f}s",
            "H → reduz HP    Esc → pausar",
        ]):
            surf = f.render(line, True, (70, 80, 110))
            screen.blit(surf, (cx - surf.get_width() // 2, cy + i * 20))

        self._ui.draw(screen)

    def handle_event(self, event):
        self._ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_h:
                self._hp = max(0.0, self._hp - 10)
                self._hp_bar.set_value(self._hp)
                if self._hp <= 0:
                    SceneManager.instance().load(
                        GameOverScene(self._score),
                        FadeTransition(color=(180, 0, 0),
                                       duration_out=0.6, duration_in=0.5),
                    )
            if event.key == pygame.K_ESCAPE:
                SceneManager.instance().push(
                    PauseScene(),
                    SlideTransition(SlideDirection.UP,
                                    duration_out=0.0, duration_in=0.35),
                )


# ─── GameOverScene ────────────────────────────────────────────────────────────

class GameOverScene(Scene):
    """Tela de Game Over com score final."""

    def __init__(self, score: int = 0):
        super().__init__()
        self._final_score = score

    def start(self):
        self._ui   = UIManager.instance()
        canvas     = UICanvas(name="GameOver", z_order=0)

        panel = Panel(
            x=0, y=0, width=360, height=280,
            color=(22, 5, 5, 230),
            border_color=(200, 40, 40, 220),
            border_radius=16,
            anchor=Anchor.MIDDLE_CENTER, pivot=Pivot.MIDDLE_CENTER,
        )
        canvas.add_child(panel)

        panel.add_child(Label(
            "GAME OVER", x=0, y=20,
            font_size=32, bold=True,
            color=(220, 55, 55), shadow=True,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Label(
            f"Score final: {self._final_score}",
            x=0, y=80, font_size=20,
            color=(220, 200, 100),
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        panel.add_child(Button(
            "↺  Jogar Novamente",
            x=0, y=130, width=260, height=50,
            on_click=self._restart,
            color_normal=(50, 30, 100), color_hover=(80, 50, 160),
            font_size=18,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))
        panel.add_child(Button(
            "⌂  Menu Principal",
            x=0, y=194, width=260, height=50,
            on_click=self._to_menu,
            color_normal=(60, 20, 20), color_hover=(100, 35, 35),
            font_size=18,
            anchor=Anchor.TOP_CENTER, pivot=Pivot.TOP_CENTER,
        ))

        self._ui.add_canvas(canvas)

    def _restart(self):
        SceneManager.instance().load(
            GameScene(),
            CrossfadeTransition(duration=0.6),
        )

    def _to_menu(self):
        SceneManager.instance().load(
            TitleScene(),
            CrossfadeTransition(duration=0.5),
        )

    def update(self, dt):
        self._ui.update(dt)

    def draw(self, screen):
        screen.fill((12, 4, 4))
        self._ui.draw(screen)

    def handle_event(self, event):
        self._ui.handle_event(event, pygame.display.get_surface())
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._restart()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    engine = Engine(width=SW, height=SH,
                    title="Zennity — SceneManager Demo", fps=60)
    sm = engine.use_scene_manager()    # ← ativa o SceneManager
    engine.run(SplashScene())
