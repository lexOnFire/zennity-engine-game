from __future__ import annotations
"""
editor/editor_2d.py
───────────────────
Editor visual dedicado para criação de jogos 2D.
"""

import math
import pygame
import numpy as np
from collections import deque
from typing import List, Optional, Dict

from engine.core import Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from engine.graphics.camera2d import Camera2D
import editor.theme as T
from editor.gui import GuiButton, SectionHeader


# Cores temáticas por tipo de objeto
SHAPE_COLORS: Dict[str, tuple] = {
    "Quadrado":  (220,  80,  60),
    "Círculo":   (100, 180, 255),
    "Plataforma":(  50, 150, 100),
}


class Editor2DScene(Scene):
    def start(self) -> None:
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        # Câmera do editor 2D
        self.cam_obj = GameObject("EditorCamera")
        self.camera = self.cam_obj.add_component(Camera2D(zoom=1.0))
        self.cam_obj.transform.position = np.array([400.0, 300.0, 0.0], dtype=np.float32)
        self._add_go(self.cam_obj)
        Camera2D.main = self.camera

        # Histórico de undo/redo 2D
        self._undo_stack: deque[list] = deque(maxlen=50)
        self._redo_stack: deque[list] = deque(maxlen=50)

        # Viewport
        self.grid_size  = 32
        self.show_grid  = True
        self.vp_left    = 240
        self.vp_top     = 30
        self.vp_right   = 1140
        self.vp_bottom  = 740
        self.vp_w       = self.vp_right  - self.vp_left
        self.vp_h       = self.vp_bottom - self.vp_top

        # Play Mode
        self.playing       = False
        self.play_snapshot: Optional[list] = None

        # Panning do viewport com botão do meio
        self._panning        = False
        self._pan_last_mouse = (0, 0)

        # Drag de objetos
        self._dragging_target = None
        self._drag_offset     = np.array([0.0, 0.0])

        # Scroll da hierarquia
        self._hier_scroll = 0

        # Fontes
        self.font      = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_lg   = pygame.font.SysFont("monospace", 17, bold=True)
        self.font_sm   = pygame.font.SysFont("monospace", 11)

        # ── Botões esquerda ──────────────────────────────────────────
        _P  = T.BTN_PRIMARY; _PH = T.BTN_PRIMARY_HOVER
        _S  = T.BTN_SECONDARY; _SH = T.BTN_SECONDARY_HOVER

        self.btn_play   = GuiButton(10, 68, 105, 28, "▶  PLAY",    on_click=self.toggle_play,  bg=T.BTN_SPECIAL,    hover=T.BTN_SPECIAL_HOVER)
        self.btn_undo   = GuiButton(120, 68, 60, 28, "↩ Undo",     on_click=self.undo,          bg=_S,               hover=_SH)
        self.btn_redo   = GuiButton(185, 68, 50, 28, "↪ Redo",     on_click=self.redo,          bg=_S,               hover=_SH)
        self.btn_back   = GuiButton(10,  4,  80, 24, "← Voltar",   on_click=self._go_back,      bg=_S,               hover=_SH)
        self.btn_grid   = GuiButton(100, 4,  80, 24, "Grade: ON",  on_click=self._toggle_grid,  bg=_S,               hover=_SH)

        # Botões de adicionar formas
        self.btn_add_quad = GuiButton( 10, 320,  68, 26, "Quadrado",  on_click=lambda: self.spawn_object("Quadrado"),  bg=_P, hover=_PH)
        self.btn_add_circ = GuiButton( 82, 320,  68, 26, "Círculo",   on_click=lambda: self.spawn_object("Círculo"),   bg=_P, hover=_PH)
        self.btn_add_plat = GuiButton(154, 320,  76, 26, "Plataforma",on_click=lambda: self.spawn_object("Plataforma"),bg=_P, hover=_PH)
        self.btn_delete   = GuiButton( 10, 352, 220, 26, "✕ Excluir Selecionado", on_click=self.delete_selected, bg=T.BTN_DANGER, hover=T.BTN_DANGER_HOVER)

        self._all_buttons = [
            self.btn_play, self.btn_undo, self.btn_redo, self.btn_back, self.btn_grid,
            self.btn_add_quad, self.btn_add_circ, self.btn_add_plat, self.btn_delete,
        ]

        self.spawn_default_scene()

    # ------------------------------------------------------------------
    # Helpers de coordenada
    # ------------------------------------------------------------------

    def _world_to_vp(self, world_pos: np.ndarray) -> tuple:
        if Camera2D.main is None:
            return float(world_pos[0]), float(world_pos[1])
        sx, sy = Camera2D.main.world_to_screen(world_pos, self.vp_w, self.vp_h)
        return sx + self.vp_left, sy + self.vp_top

    def _vp_to_world(self, mx: float, my: float) -> np.ndarray:
        if Camera2D.main is None:
            return np.array([mx, my, 0.0], dtype=np.float32)
        wx, wy = Camera2D.main.screen_to_world(
            (mx - self.vp_left, my - self.vp_top),
            self.vp_w, self.vp_h,
        )
        return np.array([wx, wy, 0.0], dtype=np.float32)

    def _in_viewport(self, mx: float, my: float) -> bool:
        return self.vp_left < mx < self.vp_right and self.vp_top < my < self.vp_bottom

    # ------------------------------------------------------------------
    # Cena padrão
    # ------------------------------------------------------------------

    def spawn_default_scene(self) -> None:
        floor = GameObject("Chão")
        floor.transform.position = np.array([400.0, 500.0, 0.0], dtype=np.float32)
        floor.transform.scale    = np.array([600.0,  32.0, 1.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32))
        rb = floor.add_component(RigidBody()); rb.is_kinematic = True
        floor.mesh_type = "Plataforma"
        self._add_go(floor); self.editable_objects.append(floor)

        box = GameObject("Caixa")
        box.transform.position = np.array([400.0, 200.0, 0.0], dtype=np.float32)
        box.transform.scale    = np.array([ 40.0,  40.0, 1.0], dtype=np.float32)
        box.add_component(BoxCollider(width=40, height=40))
        box.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        box.mesh_type = "Quadrado"
        self._add_go(box); self.editable_objects.append(box)

        self.selected_index = 1

    # ------------------------------------------------------------------
    # Gerenciamento de GameObjects
    # ------------------------------------------------------------------

    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        if go not in self.game_objects:
            self.game_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def spawn_object(self, shape: str) -> None:
        if self.playing:
            return
        self._push2d()
        center = self._vp_to_world(self.vp_left + self.vp_w / 2, self.vp_top + self.vp_h / 2)
        go = GameObject(f"Obj_{shape}_{len(self.editable_objects)}")
        go.transform.position = center.copy() if len(center) == 3 else np.array([center[0], center[1], 0.0], dtype=np.float32)
        if shape == "Quadrado":
            go.transform.scale = np.array([40.0, 40.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=40, height=40))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Círculo":
            go.transform.scale = np.array([40.0, 40.0, 1.0], dtype=np.float32)
            go.add_component(CircleCollider(radius=20))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Plataforma":
            go.transform.scale = np.array([120.0, 24.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=120, height=24))
            rb = go.add_component(RigidBody()); rb.is_kinematic = True
        go.mesh_type = shape
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1

    def delete_selected(self) -> None:
        if self.playing or self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return
        self._push2d()
        obj = self.editable_objects.pop(self.selected_index)
        self._remove_go(obj)
        self.selected_index = max(0, self.selected_index - 1) if self.editable_objects else -1

    # ------------------------------------------------------------------
    # Snapshot 2D (independente do History 3D)
    # ------------------------------------------------------------------

    def _snap2d(self) -> list:
        snap = []
        for obj in self.editable_objects:
            snap.append({
                "name":      obj.name,
                "mesh_type": obj.mesh_type,
                "pos":       obj.transform.position.copy(),
                "scale":     obj.transform.scale.copy(),
            })
        return snap

    def _restore2d(self, snap: list) -> None:
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        for s in snap:
            self._create_obj(s["name"], s["mesh_type"], s["pos"], s["scale"])
        self.selected_index = min(self.selected_index, len(self.editable_objects) - 1)

    def _push2d(self) -> None:
        self._undo_stack.append(self._snap2d())
        self._redo_stack.clear()

    def _create_obj(self, name: str, shape: str, pos: np.ndarray, scale: np.ndarray) -> GameObject:
        go = GameObject(name)
        # Garante que posição e escala sempre tenham 3 componentes
        go.transform.position = np.array([pos[0], pos[1], 0.0], dtype=np.float32)
        go.transform.scale    = np.array([scale[0], scale[1], 1.0], dtype=np.float32)
        if shape == "Quadrado":
            go.add_component(BoxCollider(width=int(scale[0]), height=int(scale[1])))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Círculo":
            go.add_component(CircleCollider(radius=max(1, int(scale[0] / 2))))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Plataforma":
            go.add_component(BoxCollider(width=int(scale[0]), height=int(scale[1])))
            rb = go.add_component(RigidBody()); rb.is_kinematic = True
        go.mesh_type = shape
        self._add_go(go)
        self.editable_objects.append(go)
        return go

    # ------------------------------------------------------------------
    # Play / Undo / Redo
    # ------------------------------------------------------------------

    def undo(self) -> None:
        if self.playing or not self._undo_stack:
            return
        self._redo_stack.append(self._snap2d())
        self._restore2d(self._undo_stack.pop())

    def redo(self) -> None:
        if self.playing or not self._redo_stack:
            return
        self._undo_stack.append(self._snap2d())
        self._restore2d(self._redo_stack.pop())

    def toggle_play(self) -> None:
        if not self.playing:
            self.play_snapshot = self._snap2d()
            self.playing = True
            self.btn_play.text        = "■  STOP"
            self.btn_play.bg_color    = T.BTN_DANGER
            self.btn_play.hover_color = T.BTN_DANGER_HOVER
        else:
            self.playing = False
            self.btn_play.text        = "▶  PLAY"
            self.btn_play.bg_color    = T.BTN_SPECIAL
            self.btn_play.hover_color = T.BTN_SPECIAL_HOVER
            if self.play_snapshot is not None:
                self._restore2d(self.play_snapshot)
                self.play_snapshot = None

    def _go_back(self) -> None:
        if self.playing:
            self.toggle_play()
        from editor.launcher import LauncherScene
        if self.engine:
            self.engine.change_scene(LauncherScene())

    def _toggle_grid(self) -> None:
        self.show_grid = not self.show_grid
        self.btn_grid.text = "Grade: ON" if self.show_grid else "Grade: OFF"

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self.playing:
            for go in self.game_objects:
                go.update(dt)
            BoxCollider.check_all()
            CircleCollider.check_all()

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def handle_event(self, event: pygame.event.Event) -> None:
        mx, my = pygame.mouse.get_pos()

        # ── Atalhos de teclado ─────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
            elif event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                self.delete_selected()
            elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.undo()
            elif event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.redo()
            elif event.key == pygame.K_F1:
                self._toggle_grid()

        # ── Scroll: zoom do viewport ────────────────────────────────
        elif event.type == pygame.MOUSEWHEEL:
            if self._in_viewport(mx, my):
                factor = 1.1 if event.y > 0 else 0.9
                if Camera2D.main:
                    Camera2D.main.zoom = max(0.2, min(5.0, Camera2D.main.zoom * factor))

        # ── Mouse button down ───────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Botão do meio = iniciar panning
            if event.button == 2 and self._in_viewport(mx, my):
                self._panning = True
                self._pan_last_mouse = (mx, my)
                return

            if event.button == 1:
                # Verifica todos os botões da UI
                for btn in self._all_buttons:
                    if btn.rect.collidepoint(mx, my):
                        btn.click()
                        return

                # Clique na lista de hierarquia
                if 10 < mx < 230:
                    hier_y_start = 410
                    for i, obj in enumerate(self.editable_objects):
                        yp = hier_y_start + (i - self._hier_scroll) * 22
                        if 0 < yp < 730 and yp <= my < yp + 20:
                            self.selected_index = i
                            return

                # Hit-test no viewport
                if self._in_viewport(mx, my):
                    world_click = self._vp_to_world(mx, my)
                    clicked_any = False
                    for idx, obj in enumerate(self.editable_objects):
                        opos   = obj.transform.position
                        oscale = obj.transform.scale
                        if obj.mesh_type == "Círculo":
                            hit = math.hypot(world_click[0] - opos[0], world_click[1] - opos[1]) <= oscale[0] / 2
                        else:
                            hit = (abs(world_click[0] - opos[0]) <= oscale[0] / 2 and
                                   abs(world_click[1] - opos[1]) <= oscale[1] / 2)
                        if hit:
                            self.selected_index = idx
                            if not self.playing:
                                self._dragging_target = obj
                                self._drag_offset = opos.copy() - world_click
                            clicked_any = True
                            break
                    if not clicked_any:
                        self.selected_index = -1

        # ── Mouse motion ────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            if self._panning and Camera2D.main:
                zoom = Camera2D.main.zoom
                dx = (mx - self._pan_last_mouse[0]) / zoom
                dy = (my - self._pan_last_mouse[1]) / zoom
                Camera2D.main.transform.position[0] -= dx
                Camera2D.main.transform.position[1] -= dy
                self._pan_last_mouse = (mx, my)
            elif self._dragging_target and not self.playing:
                world_pos = self._vp_to_world(mx, my)
                self._dragging_target.transform.position[0] = world_pos[0] + self._drag_offset[0]
                self._dragging_target.transform.position[1] = world_pos[1] + self._drag_offset[1]

        # ── Mouse button up ─────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self._panning = False
            if event.button == 1 and self._dragging_target:
                self._push2d()
                self._dragging_target = None

        # ── Scroll da hierarquia (botão direito sobre painel) ───────
        elif event.type == pygame.MOUSEWHEEL:
            if mx < self.vp_left:
                max_scroll = max(0, len(self.editable_objects) - 14)
                self._hier_scroll = max(0, min(max_scroll, self._hier_scroll - event.y))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(T.BG)

        # ── Viewport ────────────────────────────────────────────────
        vp_rect = pygame.Rect(self.vp_left, self.vp_top, self.vp_w, self.vp_h)
        pygame.draw.rect(screen, T.VIEWPORT_BG, vp_rect)
        screen.set_clip(vp_rect)

        zoom = Camera2D.main.zoom if Camera2D.main else 1.0
        cam_pos = Camera2D.main.transform.position if Camera2D.main else np.zeros(2)

        # Grade alinhada à câmera
        if self.show_grid:
            gs = max(8, int(self.grid_size * zoom))
            off_x = int(self.vp_left + (self.vp_w / 2) - cam_pos[0] * zoom) % gs
            off_y = int(self.vp_top  + (self.vp_h / 2) - cam_pos[1] * zoom) % gs
            grid_col = T.alpha_blend(T.BORDER, 0.12)
            for x in range(self.vp_left + off_x - gs, self.vp_right + gs, gs):
                pygame.draw.line(screen, grid_col, (x, self.vp_top), (x, self.vp_bottom))
            for y in range(self.vp_top + off_y - gs, self.vp_bottom + gs, gs):
                pygame.draw.line(screen, grid_col, (self.vp_left, y), (self.vp_right, y))
            # Eixo central (origem)
            ox, oy = self._world_to_vp(np.array([0.0, 0.0]))
            if self.vp_left < ox < self.vp_right:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_Y, 0.4), (int(ox), self.vp_top), (int(ox), self.vp_bottom))
            if self.vp_top < oy < self.vp_bottom:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_X, 0.4), (self.vp_left, int(oy)), (self.vp_right, int(oy)))

        # Objetos
        for idx, obj in enumerate(self.editable_objects):
            pos   = obj.transform.position
            scale = obj.transform.scale
            sx, sy = self._world_to_vp(pos)
            sw, sh = scale[0] * zoom, scale[1] * zoom

            if sx + sw/2 < self.vp_left or sx - sw/2 > self.vp_right:
                continue
            if sy + sh/2 < self.vp_top or sy - sh/2 > self.vp_bottom:
                continue

            selected = (idx == self.selected_index)
            base_col  = SHAPE_COLORS.get(obj.mesh_type, (180, 180, 180))
            draw_col  = T.ACCENT if selected else base_col

            if obj.mesh_type == "Círculo":
                r = max(1, int(scale[0] / 2 * zoom))
                # Fill com alfa simulado
                surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*draw_col, 200), (r, r), r)
                pygame.draw.circle(surf, (*T.BORDER, 255), (r, r), r, 2)
                screen.blit(surf, (int(sx) - r, int(sy) - r))
                if selected:
                    pygame.draw.circle(screen, T.ACCENT, (int(sx), int(sy)), r + 4, 2)
            else:
                rect = pygame.Rect(int(sx - sw/2), int(sy - sh/2), int(sw), int(sh))
                # Fill com alfa
                surf = pygame.Surface((int(sw), int(sh)), pygame.SRCALPHA)
                surf.fill((*draw_col, 200))
                screen.blit(surf, rect.topleft)
                pygame.draw.rect(screen, T.BORDER, rect, 2, border_radius=4)
                if selected:
                    sel = rect.inflate(6, 6)
                    pygame.draw.rect(screen, T.ACCENT, sel, 2, border_radius=6)

            # Rótulo do objeto
            name_surf = self.font_sm.render(obj.name, True, T.TEXT_PRIMARY)
            screen.blit(name_surf, (int(sx) - name_surf.get_width()//2, int(sy - sh/2) - 16))

        screen.set_clip(None)
        pygame.draw.rect(screen, T.BORDER, vp_rect, 2)

        # Indicador de zoom
        zoom_lbl = self.font_sm.render(f"Zoom: {zoom:.2f}x  |  Câmera: ({cam_pos[0]:.0f}, {cam_pos[1]:.0f})", True, T.TEXT_MUTED)
        screen.blit(zoom_lbl, (self.vp_left + 10, self.vp_top + 8))

        # ── Painel Esquerdo ──────────────────────────────────────────
        pygame.draw.rect(screen, T.PANEL, (0, 0, 240, 800))
        pygame.draw.line(screen, T.BORDER, (240, 0), (240, 800))

        # Título
        lbl = self.font_lg.render("EDITOR 2D", True, T.ACCENT)
        screen.blit(lbl, (10, 36))

        # Botões de controle
        self.btn_back.draw(screen, self.font_sm)
        self.btn_grid.draw(screen, self.font_sm)
        self.btn_play.draw(screen, self.font)
        self.btn_undo.draw(screen, self.font_sm)
        self.btn_redo.draw(screen, self.font_sm)

        # Seção Adicionar Objeto
        SectionHeader(10, 300, 220, "Adicionar Objeto").draw(screen, self.font_sm)
        self.btn_add_quad.draw(screen, self.font_sm)
        self.btn_add_circ.draw(screen, self.font_sm)
        self.btn_add_plat.draw(screen, self.font_sm)
        self.btn_delete.draw(screen, self.font_sm)

        # Hierarquia
        SectionHeader(10, 388, 220, f"Hierarquia ({len(self.editable_objects)} objetos)").draw(screen, self.font_sm)
        hier_y_start = 410
        visible_rows = (730 - hier_y_start) // 22
        for i in range(self._hier_scroll, min(len(self.editable_objects), self._hier_scroll + visible_rows)):
            obj  = self.editable_objects[i]
            y_px = hier_y_start + (i - self._hier_scroll) * 22
            is_sel = (i == self.selected_index)
            if is_sel:
                pygame.draw.rect(screen, T.ACCENT_BG, (8, y_px - 1, 224, 20), border_radius=3)
            dot_col = SHAPE_COLORS.get(obj.mesh_type, T.TEXT_MUTED)
            pygame.draw.circle(screen, dot_col, (18, y_px + 8), 5)
            lbl = self.font.render(obj.name, True, T.TEXT_PRIMARY if is_sel else T.TEXT_MUTED)
            screen.blit(lbl, (28, y_px))

        # ── Painel Direito (Inspector) ───────────────────────────────
        pygame.draw.rect(screen, T.PANEL, (1140, 0, 260, 800))
        pygame.draw.line(screen, T.BORDER, (1140, 0), (1140, 800))

        SectionHeader(1155, 10, 230, "Inspector").draw(screen, self.font_sm)

        if 0 <= self.selected_index < len(self.editable_objects):
            obj = self.editable_objects[self.selected_index]
            rb  = obj.get_component(RigidBody)
            col = SHAPE_COLORS.get(obj.mesh_type, (180,180,180))

            # Color chip
            pygame.draw.rect(screen, col, (1155, 30, 14, 14), border_radius=3)
            n_lbl = self.font_bold.render(obj.name, True, T.TEXT_PRIMARY)
            screen.blit(n_lbl, (1175, 30))

            insp_rows = [
                ("Tipo",     obj.mesh_type or "—"),
                ("Pos X",   f"{obj.transform.position[0]:.1f}"),
                ("Pos Y",   f"{obj.transform.position[1]:.1f}"),
                ("Tam X",   f"{obj.transform.scale[0]:.1f}"),
                ("Tam Y",   f"{obj.transform.scale[1]:.1f}"),
            ]
            if rb:
                insp_rows += [
                    ("Massa",       f"{rb.mass:.1f}"),
                    ("Gravidade",   f"{rb.gravity_scale:.1f}"),
                    ("Cinemático",  "Sim" if rb.is_kinematic else "Não"),
                ]
                if self.playing:
                    insp_rows += [
                        ("Vel X", f"{rb.velocity[0]:.1f}"),
                        ("Vel Y", f"{rb.velocity[1]:.1f}"),
                    ]

            for row_i, (k, v) in enumerate(insp_rows):
                ry = 52 + row_i * 24
                k_lbl = self.font_sm.render(k, True, T.TEXT_MUTED)
                v_lbl = self.font.render(v, True, T.TEXT_PRIMARY)
                screen.blit(k_lbl, (1158, ry))
                screen.blit(v_lbl, (1230, ry))
                pygame.draw.line(screen, T.BORDER_SOFT, (1155, ry + 20), (1375, ry + 20))
        else:
            lbl = self.font.render("Nenhum objeto selecionado", True, T.TEXT_FAINT)
            screen.blit(lbl, (1158, 38))

        # ── Status Bar ───────────────────────────────────────────────
        pygame.draw.rect(screen, T.PANEL, (240, 740, 900, 60))
        pygame.draw.line(screen, T.BORDER, (240, 740), (1140, 740))

        mode_col = (80, 220, 100) if self.playing else T.TEXT_MUTED
        mode_txt = "● SIMULANDO — física ativa" if self.playing else "○ Modo Edição"
        screen.blit(self.font_bold.render(mode_txt, True, mode_col), (260, 755))

        hints = "Del=Excluir  Ctrl+Z=Undo  Ctrl+Y=Redo  Scroll=Zoom  Botão do Meio=Panning  F1=Grade"
        screen.blit(self.font_sm.render(hints, True, T.TEXT_FAINT), (260, 772))
