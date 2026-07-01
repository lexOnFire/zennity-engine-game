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

from engine.core import Scene
from engine.game_object import GameObject
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

        # Câmera do editor 2D — posicionada no centro do viewport
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

        # Limites do viewport em pixels de tela
        self.vp_left   = 240
        self.vp_top    = 60
        self.vp_right  = 1140
        self.vp_bottom = 740
        self.vp_w = self.vp_right  - self.vp_left   # 900
        self.vp_h = self.vp_bottom - self.vp_top     # 680

        # Estados de Simulação (Play Mode)
        self.playing = False
        self.play_snapshot: Optional[Dict] = None

        # Fontes de texto
        self.font = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_large = pygame.font.SysFont("monospace", 18, bold=True)

        # Botões do Painel Esquerdo (Adicionar Objetos 2D)
        self.buttons = []
        self.buttons.append(GuiButton(20, 240, 90, 30, "Quadrado", on_click=lambda: self.spawn_object("Quadrado"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))
        self.buttons.append(GuiButton(120, 240, 90, 30, "Círculo", on_click=lambda: self.spawn_object("Círculo"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))
        self.buttons.append(GuiButton(20, 280, 90, 30, "Plataforma", on_click=lambda: self.spawn_object("Plataforma"), bg=T.BTN_PRIMARY, hover=T.BTN_PRIMARY_HOVER))

        # Controle de Simulação
        self.btn_play = GuiButton(20, 80, 90, 32, "PLAY", on_click=self.toggle_play, bg=T.BTN_SPECIAL, hover=T.BTN_SPECIAL_HOVER)
        self.btn_undo = GuiButton(120, 80, 90, 32, "Desfazer", on_click=self.undo, bg=T.BTN_SECONDARY, hover=T.BTN_SECONDARY_HOVER)

        self._dragging_target = None
        self._drag_offset = np.array([0.0, 0.0])

        self.spawn_default_scene()

    # ------------------------------------------------------------------
    # Helpers de coordenada
    # ------------------------------------------------------------------

    def _world_to_vp(self, world_pos: np.ndarray) -> tuple[float, float]:
        """Converte posição de mundo para coordenadas de tela dentro do viewport."""
        if Camera2D.main is None:
            return float(world_pos[0]), float(world_pos[1])
        sx, sy = Camera2D.main.world_to_screen(world_pos, self.vp_w, self.vp_h)
        return sx + self.vp_left, sy + self.vp_top

    def _vp_to_world(self, mx: float, my: float) -> np.ndarray:
        """Converte coordenadas de tela (mouse) para posição de mundo."""
        if Camera2D.main is None:
            return np.array([mx, my], dtype=np.float32)
        wx, wy = Camera2D.main.screen_to_world(
            (mx - self.vp_left, my - self.vp_top),
            self.vp_w,
            self.vp_h,
        )
        return np.array([wx, wy], dtype=np.float32)

    # ------------------------------------------------------------------
    # Cena padrão
    # ------------------------------------------------------------------

    def spawn_default_scene(self) -> None:
        floor = GameObject("Chão")
        floor.transform.position = np.array([400.0, 500.0], dtype=np.float32)
        floor.transform.scale    = np.array([600.0,  32.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32, is_trigger=False))
        rb = floor.add_component(RigidBody())
        rb.is_kinematic = True
        floor.mesh_type = "Plataforma"
        self._add_go(floor)
        self.editable_objects.append(floor)

        box = GameObject("Caixa")
        box.transform.position = np.array([400.0, 200.0], dtype=np.float32)
        box.transform.scale    = np.array([ 40.0,  40.0], dtype=np.float32)
        box.add_component(BoxCollider(width=40, height=40, is_trigger=False))
        box.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        box.mesh_type = "Quadrado"
        self._add_go(box)
        self.editable_objects.append(box)

        self.selected_index = 1

    # ------------------------------------------------------------------
    # Gerenciamento de GameObjects
    # ------------------------------------------------------------------

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

        center = self._vp_to_world(
            self.vp_left + self.vp_w / 2,
            self.vp_top  + self.vp_h / 2,
        )

        go = GameObject(f"Obj_{shape}_{len(self.editable_objects)}")
        go.transform.position = center.copy()

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

    # ------------------------------------------------------------------
    # Play / Undo
    # ------------------------------------------------------------------

    def undo(self) -> None:
        if self.playing:
            return
        self.history.undo(self)

    def toggle_play(self) -> None:
        if not self.playing:
            self.play_snapshot = self.history._snap(self)
            self.playing = True
            self.btn_play.text  = "STOP"
            self.btn_play.bg    = T.BTN_DANGER
            self.btn_play.hover = T.BTN_DANGER_HOVER
        else:
            self.playing = False
            self.btn_play.text  = "PLAY"
            self.btn_play.bg    = T.BTN_SPECIAL
            self.btn_play.hover = T.BTN_SPECIAL_HOVER
            if self.play_snapshot:
                self.history._restore(self, self.play_snapshot)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.playing:
            for go in self.game_objects:
                go.update(dt)
            # FIX #3 — ambos os métodos existem e são seguros de chamar
            BoxCollider.check_all()
            CircleCollider.check_all()

        mx, my = pygame.mouse.get_pos()
        self.btn_play.update(mx, my)
        self.btn_undo.update(mx, my)
        for btn in self.buttons:
            btn.update(mx, my)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        mx, my = pygame.mouse.get_pos()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.playing:
                    self.toggle_play()
                from editor.launcher import LauncherScene
                if self.engine:
                    self.engine.change_scene(LauncherScene())

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

                # Hit-test em coordenadas de MUNDO (FIX #2)
                if self.vp_left < mx < self.vp_right and self.vp_top < my < self.vp_bottom:
                    world_click = self._vp_to_world(mx, my)
                    clicked_any = False

                    for idx, obj in enumerate(self.editable_objects):
                        opos   = obj.transform.position
                        oscale = obj.transform.scale

                        if obj.mesh_type == "Círculo":
                            dist = math.hypot(world_click[0] - opos[0], world_click[1] - opos[1])
                            hit = dist <= oscale[0] / 2
                        else:
                            hit = (
                                abs(world_click[0] - opos[0]) <= oscale[0] / 2 and
                                abs(world_click[1] - opos[1]) <= oscale[1] / 2
                            )

                        if hit:
                            self.selected_index = idx
                            if not self.playing:
                                self._dragging_target = obj
                                self._drag_offset = opos.copy() - world_click
                            clicked_any = True
                            break

                    if not clicked_any:
                        self.selected_index = -1

        elif event.type == pygame.MOUSEMOTION:
            if self._dragging_target and not self.playing:
                world_pos = self._vp_to_world(mx, my)
                self._dragging_target.transform.position[0] = world_pos[0] + self._drag_offset[0]
                self._dragging_target.transform.position[1] = world_pos[1] + self._drag_offset[1]

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self._dragging_target:
                self._dragging_target = None
                self.history.push(self)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(T.BG)

        # ── Viewport central ───────────────────────────────────────
        viewport_rect = pygame.Rect(self.vp_left, self.vp_top, self.vp_w, self.vp_h)
        pygame.draw.rect(screen, T.VIEWPORT_BG, viewport_rect)
        pygame.draw.rect(screen, T.BORDER, viewport_rect, 2)

        # Clip para não vazar renderização fora do viewport
        screen.set_clip(viewport_rect)

        # Grade
        if self.show_grid:
            for x in range(self.vp_left, self.vp_right, self.grid_size):
                pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.1), (x, self.vp_top), (x, self.vp_bottom), 1)
            for y in range(self.vp_top, self.vp_bottom, self.grid_size):
                pygame.draw.line(screen, T.alpha_blend(T.BORDER, 0.1), (self.vp_left, y), (self.vp_right, y), 1)

        zoom = Camera2D.main.zoom if Camera2D.main else 1.0

        # Renderização via câmera (FIX #1)
        for idx, obj in enumerate(self.editable_objects):
            pos   = obj.transform.position
            scale = obj.transform.scale

            sx, sy = self._world_to_vp(pos)
            sw = scale[0] * zoom
            sh = scale[1] * zoom

            # Culling dentro do viewport com margem
            if sx + sw / 2 < self.vp_left or sx - sw / 2 > self.vp_right:
                continue
            if sy + sh / 2 < self.vp_top  or sy - sh / 2 > self.vp_bottom:
                continue

            color = (50, 150, 255) if obj.mesh_type == "Plataforma" else (220, 80, 60)
            if idx == self.selected_index:
                color = T.ACCENT

            if obj.mesh_type == "Círculo":
                r = max(1, int(scale[0] / 2 * zoom))
                pygame.draw.circle(screen, color, (int(sx), int(sy)), r)
                pygame.draw.circle(screen, T.BORDER, (int(sx), int(sy)), r, 2)
            else:
                rect = pygame.Rect(int(sx - sw / 2), int(sy - sh / 2), int(sw), int(sh))
                pygame.draw.rect(screen, color, rect, border_radius=4)
                pygame.draw.rect(screen, T.BORDER, rect, 2, border_radius=4)

            # Anel de seleção
            if idx == self.selected_index:
                if obj.mesh_type == "Círculo":
                    r = max(1, int(scale[0] / 2 * zoom))
                    pygame.draw.circle(screen, T.ACCENT, (int(sx), int(sy)), r + 3, 2)
                else:
                    sel_rect = pygame.Rect(int(sx - sw / 2) - 3, int(sy - sh / 2) - 3, int(sw) + 6, int(sh) + 6)
                    pygame.draw.rect(screen, T.ACCENT, sel_rect, 2, border_radius=6)

        screen.set_clip(None)

        # ── Painel Esquerdo ──────────────────────────────────────
        left_panel = pygame.Rect(0, 0, 240, 800)
        pygame.draw.rect(screen, T.PANEL, left_panel)
        pygame.draw.line(screen, T.BORDER, (240, 0), (240, 800), 1)

        title_lbl = self.font_large.render("EDITOR 2D", True, T.ACCENT)
        screen.blit(title_lbl, (20, 20))

        self.btn_play.draw(screen)
        self.btn_undo.draw(screen)

        SectionHeader(20, 130, "Lista de Hierarquia").draw(screen)
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

        # ── Painel Direito (Inspector) ───────────────────────────
        right_panel = pygame.Rect(1140, 0, 260, 800)
        pygame.draw.rect(screen, T.PANEL, right_panel)
        pygame.draw.line(screen, T.BORDER, (1140, 0), (1140, 800), 1)

        SectionHeader(1160, 20, "Inspector (Propriedades)").draw(screen)

        if 0 <= self.selected_index < len(self.editable_objects):
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

            for idx2, line in enumerate(lines):
                lbl = self.font.render(line, True, T.TEXT_PRIMARY)
                screen.blit(lbl, (1165, 60 + idx2 * 24))
        else:
            lbl = self.font.render("Nenhum objeto selecionado", True, T.TEXT_MUTED)
            screen.blit(lbl, (1165, 60))

        # ── Status Bar ─────────────────────────────────────────────
        status_rect = pygame.Rect(240, 740, 900, 60)
        pygame.draw.rect(screen, T.PANEL, status_rect)
        pygame.draw.line(screen, T.BORDER, (240, 740), (1140, 740), 1)

        mode_lbl = self.font_bold.render(
            "● SIMULANDO" if self.playing else "○ Edição",
            True,
            (80, 220, 100) if self.playing else T.TEXT_MUTED,
        )
        screen.blit(mode_lbl, (260, 762))

        hint_lbl = self.font.render(
            "Arraste objetos para posicionar  |  ESC = Launcher  |  Scroll = Zoom (em breve)",
            True, T.TEXT_MUTED,
        )
        screen.blit(hint_lbl, (400, 762))
