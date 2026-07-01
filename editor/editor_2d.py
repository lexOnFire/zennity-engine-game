from __future__ import annotations
"""
editor/editor_2d.py
───────────────────
Editor visual dedicado inteiramente para criação de jogos 2D.
"""

import sys
import math
import random
import pygame
import numpy as np
from typing import List, Optional, Any, Dict

from engine.core import Scene, GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from engine.graphics.camera2d import Camera2D
from engine.graphics.renderer2d import SpriteRenderer
import editor.theme as T
from editor.gui import GuiButton, SectionHeader
from editor.history import History
from editor.layout_constants import *


class Editor2DScene(Scene):
    def start(self) -> None:
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        # Câmera do editor 2D
        self.cam_obj = GameObject("EditorCamera")
        self.camera = self.cam_obj.add_component(Camera2D(zoom=1.0))
        self.cam_obj.transform.position = np.array([400.0, 300.0], dtype=np.float32)
        self.add_game_object(self.cam_obj)
        Camera2D.main = self.camera

        # Histórico para desfazer/refazer
        self.history = History()

        # Configurações do Viewport 2D
        self.grid_size = 32
        self.show_grid = True
        self.show_debug_physics = True

        # Estados de Simulação (Play Mode)
        self.playing = False
        self.play_snapshot: Optional[Dict] = None

        # Fontes de texto
        self.font = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_large = pygame.font.SysFont("monospace", 18, bold=True)

        # Botões do Painel Esquerdo (Adicionar Objetos 2D)
        self.buttons = []
        self.buttons.append(GuiButton("Quadrado", 20, 240, 90, 30, on_click=lambda: self.spawn_object("Quadrado"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))
        self.buttons.append(GuiButton("Círculo", 120, 240, 90, 30, on_click=lambda: self.spawn_object("Círculo"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))
        self.buttons.append(GuiButton("Plataforma", 20, 280, 90, 30, on_click=lambda: self.spawn_object("Plataforma"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))

        # Controle de Simulação
        self.btn_play = GuiButton("PLAY", 20, 80, 90, 32, on_click=self.toggle_play, bg=T.BTN_SPECIAL, hover=T.BTN_SPECIAL_HOVER)
        self.btn_undo = GuiButton("Desfazer", 120, 80, 90, 32, on_click=self.undo, bg=T.BTN_SECONDARY, hover=T.BTN_SECONDARY_HOVER)

        self._dragging_target = None
        self._drag_offset = np.array([0.0, 0.0])

        self.spawn_default_scene()

    def spawn_default_scene(self) -> None:
        # Cria um chão estático
        floor = GameObject("Chão")
        floor.transform.position = np.array([400.0, 500.0], dtype=np.float32)
        floor.transform.scale = np.array([600.0, 32.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32, is_trigger=False))
        rb = floor.add_component(RigidBody())
        rb.is_kinematic = True
        floor.mesh_type = "Plataforma"
        self._add_go(floor)
        self.editable_objects.append(floor)

        # Cria uma caixa caindo
        box = GameObject("Caixa")
        box.transform.position = np.array([400.0, 200.0], dtype=np.float32)
        box.transform.scale = np.array([40.0, 40.0], dtype=np.float32)
        box.add_component(BoxCollider(width=40, height=40, is_trigger=False))
        box.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        box.mesh_type = "Quadrado"
        self._add_go(box)
        self.editable_objects.append(box)

        self.selected_index = 1

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)

    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def spawn_object(self, shape: str) -> None:
        if self.playing:
            return
        
        go = GameObject(f"Obj_{shape}_{len(self.editable_objects)}")
        go.transform.position = np.array([400.0, 300.0], dtype=np.float32)
        
        if shape == "Quadrado":
            go.transform.scale = np.array([40.0, 40.0], dtype=np.float32)
            go.add_component(BoxCollider(width=40, height=40))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Círculo":
            go.transform.scale = np.array([40.0, 40.0], dtype=np.float32)
            go.add_component(CircleCollider(radius=20))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Plataforma":
            go.transform.scale = np.array([120.0, 24.0], dtype=np.float32)
            go.add_component(BoxCollider(width=120, height=24))
            rb = go.add_component(RigidBody())
            rb.is_kinematic = True
            
        go.mesh_type = shape
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self.history.push(self)

    def undo(self) -> None:
        if self.playing:
            return
        self.history.undo(self)

    def toggle_play(self) -> None:
        if not self.playing:
            # Salva estado atual
            self.play_snapshot = self.history._snap(self)
            self.playing = True
            self.btn_play.text = "STOP"
            self.btn_play.bg = T.BTN_DANGER
            self.btn_play.hover = T.BTN_DANGER_HOVER
        else:
            self.playing = False
            self.btn_play.text = "PLAY"
            self.btn_play.bg = T.BTN_SPECIAL
            self.btn_play.hover = T.BTN_SPECIAL_HOVER
            # Restaura estado
            if self.play_snapshot:
                self.history._restore(self, self.play_snapshot)

    def update(self, dt: float) -> None:
        # Se estiver simulando, roda a física da engine
        if self.playing:
            # Step do physics simulator integrado
            for go in self.game_objects:
                go.update(dt)
            BoxCollider.check_all()
            CircleCollider.check_all()

        # Update botões
        mx, my = pygame.mouse.get_pos()
        self.btn_play.update(mx, my)
        self.btn_undo.update(mx, my)
        for btn in self.buttons:
            btn.update(mx, my)

    def handle_event(self, event: pygame.event.Event) -> None:
        mx, my = pygame.mouse.get_pos()

        # Botão voltar para launcher
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.playing:
                    self.toggle_play()
                from editor.launcher import LauncherScene
                if self.engine:
                    self.engine.change_scene(LauncherScene())

        # Clique nos botões
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.btn_play.rect.collidepoint(mx, my):
                    self.btn_play.click()
                    return
                if self.btn_undo.rect.collidepoint(mx, my):
                    self.btn_undo.click()
                    return
                for btn in self.buttons:
                    if btn.rect.collidepoint(mx, my):
                        btn.click()
                        return

                # Se clicou no viewport (área central), seleciona e arrasta
                if 240 < mx < 1140 and 60 < my < 740:
                    # Seleciona objeto
                    clicked_any = False
                    for idx, obj in enumerate(self.editable_objects):
                        opos = obj.transform.position
                        oscale = obj.transform.scale
                        rect = pygame.Rect(opos[0] - oscale[0]/2, opos[1] - oscale[1]/2, oscale[0], oscale[1])
                        if rect.collidepoint(mx, my):
                            self.selected_index = idx
                            self._dragging_target = obj
                            self._drag_offset = np.array([opos[0] - mx, opos[1] - my])
                            clicked_any = True
                            break
                    if not clicked_any:
                        self.selected_index = -1

        elif event.type == pygame.MOUSEMOTION:
            if self._dragging_target and not self.playing:
                self._dragging_target.transform.position[0] = mx + self._drag_offset[0]
                self._dragging_target.transform.position[1] = my + self._drag_offset[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self._dragging_target:
                self._dragging_target = None
                self.history.push(self)

    def draw(self, screen: pygame.Surface) -> None:
        # Fundo geral do Editor
        screen.fill(T.BG)

        # ── Viewport central (240 a 1140 de largura, 60 a 740 de altura)
        viewport_rect = pygame.Rect(240, 60, 900, 680)
        pygame.draw.rect(screen, T.VIEWPORT_BG, viewport_rect)
        pygame.draw.rect(screen, T.BORDER, viewport_rect, 2)

        # Grade dentro do Viewport
        if self.show_grid:
            for x in range(240, 1140, self.grid_size):
                pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.1), (x, 60), (x, 740), 1)
            for y in range(60, 740, self.grid_size):
                pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.1), (240, y), (1140, y), 1)

        # Renderização de todos os GameObjects editáveis
        for idx, obj in enumerate(self.editable_objects):
            pos = obj.transform.position
            scale = obj.transform.scale
            
            # Culling simples dentro do viewport
            if 240 < pos[0] < 1140 and 60 < pos[1] < 740:
                color = (50, 150, 255) if obj.mesh_type == "Plataforma" else (220, 80, 60)
                if idx == self.selected_index:
                    color = T.ACCENT

                rect = pygame.Rect(pos[0] - scale[0]/2, pos[1] - scale[1]/2, scale[0], scale[1])
                
                if obj.mesh_type == "Círculo":
                    pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), int(scale[0]/2))
                    pygame.draw.circle(screen, T.BORDER, (int(pos[0]), int(pos[1])), int(scale[0]/2), 2)
                else:
                    pygame.draw.rect(screen, color, rect, border_radius=4)
                    pygame.draw.rect(screen, T.BORDER, rect, 2, border_radius=4)

        # ── Painel Esquerdo (Hierarquia & Adicionar Objetos) ──
        left_panel = pygame.Rect(0, 0, 240, 800)
        pygame.draw.rect(screen, T.PANEL, left_panel)
        pygame.draw.line(screen, T.BORDER, (240, 0), (240, 800), 1)

        title_lbl = self.font_large.render("EDITOR 2D", True, T.ACCENT)
        screen.blit(title_lbl, (20, 20))

        # Desenha botões de controle e adição
        self.btn_play.draw(screen)
        self.btn_undo.draw(screen)

        SectionHeader(20, 130, "Lista de Hierarquia").draw(screen)
        # Render lista de objetos
        for i, obj in enumerate(self.editable_objects):
            y_pos = 160 + i * 22
            color = T.TEXT_PRIMARY if i == self.selected_index else T.TEXT_MUTED
            if i == self.selected_index:
                pygame.draw.rect(screen, T.ACCENT_BG, (15, y_pos - 2, 210, 20), border_radius=4)
            lbl = self.font.render(f"• {obj.name}", True, color)
            screen.blit(lbl, (25, y_pos))

        SectionHeader(20, 210, "Adicionar Objeto").draw(screen)
        for btn in self.buttons:
            btn.draw(screen)

        # ── Painel Direito (Inspector 2D) ──
        right_panel = pygame.Rect(1140, 0, 260, 800)
        pygame.draw.rect(screen, T.PANEL, right_panel)
        pygame.draw.line(screen, T.BORDER, (1140, 0), (1140, 800), 1)

        SectionHeader(1160, 20, "Inspector (Propriedades)").draw(screen)

        if self.selected_index != -1 and self.selected_index < len(self.editable_objects):
            obj = self.editable_objects[self.selected_index]
            lines = [
                f"Nome: {obj.name}",
                f"Pos X: {obj.transform.position[0]:.2f}",
                f"Pos Y: {obj.transform.position[1]:.2f}",
                f"Tam X: {obj.transform.scale[0]:.2f}",
                f"Tam Y: {obj.transform.scale[1]:.2f}",
            ]
            
            rb = obj.get_component(RigidBody)
            if rb:
                lines.append(f"Massa: {rb.mass:.1f}")
                lines.append(f"Gravidade: {rb.gravity_scale:.1f}")
                lines.append(f"Cinemático: {'Sim' if rb.is_kinematic else 'Não'}")

            for idx, line in enumerate(lines):
                lbl = self.font.render(line, True, T.TEXT_PRIMARY)
                screen.blit(lbl, (1165, 60 + idx * 24))
        else:
            lbl = self.font.render("Nenhum objeto selecionado", True, T.TEXT_MUTED)
            screen.blit(lbl, (1165, 60))

        # Status Bar / Dicas
        status_rect = pygame.Rect(240, 740, 900, 60)
        pygame.draw.rect(screen, T.PANEL, status_rect)
        pygame.draw.line(screen, T.BORDER, (240, 740), (1140, 740), 1)
        
        hint_lbl = self.font.render("Dica: Clique e arraste para posicionar. Pressione ESC para voltar ao Launcher.", True, T.TEXT_MUTED)
        screen.blit(hint_lbl, (260, 762))
