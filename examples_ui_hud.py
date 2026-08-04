"""Exemplos prontos de criação de HUDs — Use como referência!

Esses exemplos mostram como criar HUDs reais para jogos.
Copie e adapte para seu projeto!
"""

import pygame
from engine.core import Engine, Scene
from engine.ui import Anchor, Pivot
from engine.ui.hud_system import HUDSystem


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 1: RPG Simples (HP + Score)
# ════════════════════════════════════════════════════════════════════════════

class RPGScene(Scene):
    """Cena de RPG com HUD básico."""

    def start(self):
        """Inicializa a scene."""
        # Estado do jogo
        self.player_hp = 100
        self.max_hp = 100
        self.score = 0
        self.level = 1

        # ── Criar e configurar HUD ──
        self.hud = HUDSystem("RPG_HUD", z_order=0)
        self.hud.create()

        # PAINEL SUPERIOR ESQUERDO: HP + MP
        self.hud.add_health_bar(
            widget_id="hp_bar",
            x=15, y=15,
            width=180,
            height=20,
            max_health=self.max_hp,
            current_health=self.player_hp,
            label="HP",
            label_color=(240, 80, 80),
            show_text=True,
            border_radius=8,
        )

        # CANTO SUPERIOR DIREITO: Score
        self.hud.add_score_display(
            widget_id="score",
            x=-15, y=15,
            initial_score=self.score,
            anchor=Anchor.TOP_RIGHT,
            color=(255, 220, 60),
            font_size=28,
            bold=True,
        )

        # CENTRO: Level
        self.hud.add_text_label(
            widget_id="level",
            text=f"LEVEL {self.level}",
            x=0, y=0,
            font_size=18,
            color=(100, 200, 100),
            anchor=Anchor.MIDDLE_CENTER,
            bold=True,
            shadow=True,
        )

        # FUNDO: Dica
        self.hud.add_text_label(
            widget_id="hint",
            text="Press H: -10 HP | S: +100 Score | L: Level Up",
            x=0, y=-15,
            font_size=12,
            color=(160, 160, 180),
            anchor=Anchor.BOTTOM_CENTER,
        )

        # Mostrar na tela
        self.hud.show()

    def update(self, dt):
        """Atualiza a cena a cada frame."""
        keys = pygame.key.get_pressed()

        # H: Perde 10 HP
        if keys[pygame.K_h]:
            self.player_hp = max(0, self.player_hp - 10)
            self.hud.set_health("hp_bar", self.player_hp)
            if self.player_hp == 0:
                self.hud.set_text("hint", "GAME OVER! Press R to restart")

        # S: Ganha 100 de score
        if keys[pygame.K_s]:
            self.hud.add_score("score", 100)

        # L: Sobe level
        if keys[pygame.K_l]:
            self.level += 1
            self.hud.set_text("level", f"LEVEL {self.level}")

        # ESC: Sair
        if keys[pygame.K_ESCAPE]:
            self.engine.quit()

    def on_scene_end(self):
        """Limpa ao sair da cena."""
        self.hud.remove()


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 2: Shooter — HUD com Ammo + Vida + Inimigos
# ════════════════════════════════════════════════════════════════════════════

class ShooterScene(Scene):
    """Cena de shooter com HUD avançado."""

    def start(self):
        """Inicializa."""
        # Estado
        self.health = 100
        self.max_health = 100
        self.ammo = 30
        self.max_ammo = 30
        self.enemies_killed = 0

        # HUD
        self.hud = HUDSystem("Shooter_HUD").create()

        # PAINEL ESQUERDO: Health + Ammo
        self.hud.add_health_bar(
            widget_id="health",
            x=10, y=10,
            width=150,
            max_health=self.max_health,
            current_health=self.health,
            label="Health",
            label_color=(255, 100, 100),
        )

        self.hud.add_health_bar(
            widget_id="ammo",
            x=10, y=100,
            width=150,
            max_health=self.max_ammo,
            current_health=self.ammo,
            label="Ammo",
            label_color=(100, 200, 255),
            bar_color=(100, 150, 255),
            bg_color=(20, 30, 50),
        )

        # CANTO DIREITO: Inimigos mortos
        self.hud.add_score_display(
            widget_id="kills",
            x=-10, y=10,
            initial_score=0,
            anchor=Anchor.TOP_RIGHT,
            color=(200, 100, 100),
            font_size=24,
        )

        # CROSSHAIR (texto central)
        self.hud.add_text_label(
            widget_id="crosshair",
            text="+",
            x=0, y=0,
            font_size=32,
            color=(100, 255, 100),
            anchor=Anchor.MIDDLE_CENTER,
            bold=True,
        )

        self.hud.show()

    def update(self, dt):
        """Atualiza."""
        keys = pygame.key.get_pressed()

        # Disparar (usa ammo)
        if keys[pygame.K_SPACE] and self.ammo > 0:
            self.ammo -= 1
            self.hud.set_health("ammo", self.ammo)
            self.enemies_killed += 1
            self.hud.add_score("kills", 1)

        # Receber dano
        if keys[pygame.K_d]:
            self.health -= 5
            self.hud.set_health("health", self.health)

        # Recarregar
        if keys[pygame.K_r]:
            self.ammo = self.max_ammo
            self.hud.set_health("ammo", self.ammo)

    def on_scene_end(self):
        self.hud.remove()


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 3: Menu Pause com Botões
# ════════════════════════════════════════════════════════════════════════════

class GameWithPauseScene(Scene):
    """Cena com HUD de jogo + menu de pause."""

    def start(self):
        """Inicializa."""
        self.game_running = True
        self.score = 0

        # HUD DE JOGO
        self.game_hud = HUDSystem("Game_HUD", z_order=0).create()
        self.game_hud.add_score_display(
            "score", initial_score=0,
            x=-10, y=10,
            anchor=Anchor.TOP_RIGHT
        )
        self.game_hud.add_text_label(
            "hint",
            text="Space: Add Score | ESC: Pause",
            x=0, y=-15,
            font_size=12,
            anchor=Anchor.BOTTOM_CENTER,
        )
        self.game_hud.show()

        # HUD DE PAUSE (inicialmente escondido)
        self.pause_hud = HUDSystem("Pause_HUD", z_order=100).create()

        # Overlay escuro
        self.pause_hud.add_panel(
            "overlay",
            x=0, y=0, width=800, height=600,
            color=(0, 0, 0, 150),
            border_color=None,
        )

        # Janela central
        self.pause_hud.add_panel(
            "window",
            x=0, y=0, width=350, height=300,
            anchor=Anchor.MIDDLE_CENTER,
            color=(20, 20, 40, 240),
            border_color=(100, 150, 220),
            border_radius=16,
        )

        # Título
        self.pause_hud.add_text_label(
            "title",
            text="PAUSADO",
            x=0, y=30,
            font_size=28,
            color=(200, 200, 255),
            anchor=Anchor.TOP_CENTER,
            bold=True,
        )

        # Botões
        self.pause_hud.add_button(
            "resume_btn",
            "Continuar",
            on_click=self.resume_game,
            x=0, y=100,
            width=200, height=40,
            anchor=Anchor.TOP_CENTER,
            font_size=16,
        )

        self.pause_hud.add_button(
            "quit_btn",
            "Sair",
            on_click=self.quit_game,
            x=0, y=160,
            width=200, height=40,
            anchor=Anchor.TOP_CENTER,
            font_size=16,
        )

        # NÃO mostrar pause_hud ainda

    def resume_game(self):
        """Retomar o jogo."""
        self.game_running = True
        self.pause_hud.hide()

    def quit_game(self):
        """Sair do jogo."""
        self.engine.quit()

    def update(self, dt):
        """Atualiza."""
        keys = pygame.key.get_pressed()

        # ESC: Pausar/Retomar
        if keys[pygame.K_ESCAPE]:
            if self.game_running:
                self.game_running = False
                self.pause_hud.show()
            else:
                self.resume_game()

        if not self.game_running:
            return  # Não atualizar jogo enquanto pausado

        # Space: Adicionar score
        if keys[pygame.K_SPACE]:
            self.score += 1
            self.game_hud.add_score("score", 1)

    def on_scene_end(self):
        self.game_hud.remove()
        self.pause_hud.remove()


# ════════════════════════════════════════════════════════════════════════════
# EXEMPLO 4: HUD Dinâmico (FloatingText)
# ════════════════════════════════════════════════════════════════════════════

class RPGWithFloatingTextScene(Scene):
    """RPG com dano flutuante."""

    def start(self):
        self.hud = HUDSystem().create().show()
        self.hud.add_health_bar(x=10, y=10, max_health=100, current_health=100)
        self.floating_texts = []
        self.damage_counter = 0

    def add_floating_damage(self, x: float, y: float, damage: int):
        """Adiciona texto de dano flutuante."""
        text_id = f"damage_{self.damage_counter}"
        self.damage_counter += 1

        self.hud.add_text_label(
            text_id,
            text=f"-{damage}",
            x=x, y=y,
            font_size=16,
            color=(255, 100, 100),
            bold=True,
        )

        # Remover após 1 segundo
        self.floating_texts.append({
            "id": text_id,
            "lifetime": 1.0,
        })

    def update(self, dt):
        keys = pygame.key.get_pressed()

        # D: Dano
        if keys[pygame.K_d]:
            self.add_floating_damage(400, 300, 10)

        # Atualizar lifetime dos texts
        for text in self.floating_texts[:]:
            text["lifetime"] -= dt
            if text["lifetime"] <= 0:
                widget = self.hud.get_widget(text["id"])
                if widget:
                    self.hud.canvas.children.remove(widget)
                    del self.hud._widgets[text["id"]]
                self.floating_texts.remove(text)

    def on_scene_end(self):
        self.hud.remove()


# ════════════════════════════════════════════════════════════════════════════
# LAUNCHER
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Escolha qual exemplo rodar:
    EXAMPLES = {
        "1": ("RPG Simples", RPGScene),
        "2": ("Shooter", ShooterScene),
        "3": ("Menu Pause", GameWithPauseScene),
        "4": ("Floating Text", RPGWithFloatingTextScene),
    }

    print("=" * 50)
    print("Exemplos de UI/HUD")
    print("=" * 50)
    for key, (name, _) in EXAMPLES.items():
        print(f"{key}: {name}")
    print("=" * 50)

    choice = input("Escolha um exemplo (1-4): ").strip()
    if choice not in EXAMPLES:
        print("Opção inválida!")
        exit(1)

    name, scene_class = EXAMPLES[choice]
    print(f"\nRodando: {name}")
    print("Controles: H/S/L (RPG) | Space/D/R (Shooter) | ESC (Pause)")

    # Criar e rodar engine
    engine = Engine(width=800, height=600, title=f"HUD Example: {name}")
    engine.add_scene(scene_class)
    engine.run()
