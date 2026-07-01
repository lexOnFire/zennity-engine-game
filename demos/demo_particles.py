"""
demos/demo_particles.py
─────────────────────────────────────────────────────────────
Demo completa do Sistema de Partículas 2D da Zennity Engine.
"""

import sys
import os
import random
import pygame
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engine import Engine, Scene, GameObject, Camera2D
from engine.graphics.particles import ParticleSystem

SW, SH = 800, 600


class ParticlesDemoScene(Scene):
    def start(self):
        # ── Setup Câmera ──
        self.cam_obj = GameObject("Camera")
        self.camera = self.cam_obj.add_component(Camera2D())
        self.add_game_object(self.cam_obj)
        Camera2D.main = self.camera

        # ── Criar Emissor Principal
        self.emitter_obj = GameObject("Emitter")
        self.emitter_obj.transform.position = np.array([SW / 2.0, SH / 2.0], dtype=np.float32)
        
        # Preset Inicial: Fogo e Fumaça
        self.ps = self.emitter_obj.add_component(ParticleSystem(
            emission_rate=80.0,
            lifetime=1.2,
            speed=90.0,
            spread=35.0,
            start_size=10.0,
            end_size=2.0,
            start_color=(255, 170, 40),
            end_color=(40, 20, 20),
            gravity=-180.0  # Sobem como fumaça
        ))
        
        # Alinha rotação para atirar para cima
        self.emitter_obj.transform.rotation = np.array([0.0, 0.0, 270.0], dtype=np.float32)
        self.add_game_object(self.emitter_obj)

        self.preset_name = "Fogo & Fumaça"
        self.font = pygame.font.SysFont("monospace", 14)
        self.click_info = "Clique com o Mouse para Burst!"

    def set_preset(self, index: int):
        # Remove componente anterior
        self.emitter_obj.components.remove(self.ps)
        
        if index == 1:
            # Preset Fogo & Fumaça
            self.ps = self.emitter_obj.add_component(ParticleSystem(
                emission_rate=80.0, lifetime=1.2, speed=90.0, spread=35.0,
                start_size=10.0, end_size=2.0,
                start_color=(255, 170, 40), end_color=(40, 20, 20),
                gravity=-180.0
            ))
            self.emitter_obj.transform.rotation = np.array([0.0, 0.0, 270.0], dtype=np.float32)
            self.preset_name = "Fogo & Fumaça"
        elif index == 2:
            # Preset Faíscas Elétricas
            self.ps = self.emitter_obj.add_component(ParticleSystem(
                emission_rate=150.0, lifetime=0.4, speed=160.0, spread=25.0,
                start_size=4.0, end_size=1.0,
                start_color=(0, 230, 255), end_color=(0, 50, 200),
                gravity=300.0
            ))
            self.emitter_obj.transform.rotation = np.array([0.0, 0.0, 90.0], dtype=np.float32)
            self.preset_name = "Faíscas Elétricas"
        elif index == 3:
            # Preset Fonte Mágica
            self.ps = self.emitter_obj.add_component(ParticleSystem(
                emission_rate=100.0, lifetime=2.2, speed=280.0, spread=15.0,
                start_size=7.0, end_size=1.5,
                start_color=(120, 255, 180), end_color=(40, 60, 150),
                gravity=350.0
            ))
            self.emitter_obj.transform.rotation = np.array([0.0, 0.0, 270.0], dtype=np.float32)
            self.preset_name = "Fonte Mágica"
        elif index == 4:
            # Preset Chuva de Estrelas (Burst apenas)
            self.ps = self.emitter_obj.add_component(ParticleSystem(
                emission_rate=0.0, lifetime=1.5, speed=120.0, spread=360.0,
                start_size=8.0, end_size=1.0,
                start_color=(255, 235, 100), end_color=(100, 30, 150),
                gravity=100.0
            ))
            self.preset_name = "Apenas Bursts (Estrelas)"

    def update(self, dt: float):
        # Emissor segue suavemente a posição do mouse
        mx, my = pygame.mouse.get_pos()
        pos = self.emitter_obj.transform.position
        pos[0] += (mx - pos[0]) * 0.15
        pos[1] += (my - pos[1]) * 0.15

        for go in self.game_objects:
            go.update(dt)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo do mouse
                self.ps.emit(80)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.set_preset(1)
            elif event.key == pygame.K_2:
                self.set_preset(2)
            elif event.key == pygame.K_3:
                self.set_preset(3)
            elif event.key == pygame.K_4:
                self.set_preset(4)

    def draw(self, screen: pygame.Surface):
        screen.fill((10, 12, 22))

        # Desenha emissores e partículas
        for go in self.game_objects:
            go.draw(screen)

        # HUD / Instruções
        lines = [
            "Zennity Engine — Particle System Demo",
            f"Preset Ativo: {self.preset_name}",
            f"Partículas na Tela: {len(self.ps.particles)}",
            "",
            "Teclas para Presets:",
            "  1 : Fogo & Fumaça",
            "  2 : Faíscas Elétricas",
            "  3 : Fonte Mágica",
            "  4 : Apenas Bursts (Estrelas)",
            "",
            self.click_info,
        ]
        for i, line in enumerate(lines):
            color = (255, 220, 100) if "Preset Ativo" in line else (200, 200, 200)
            surf = self.font.render(line, True, color)
            screen.blit(surf, (15, 15 + i * 18))


if __name__ == "__main__":
    pygame.init()
    engine = Engine(width=SW, height=SH, title="Zennity — Particle System Demo", fps=60)
    engine.run(ParticlesDemoScene())
