from __future__ import annotations
"""
editor/editor_2d.py
───────────────────
Editor visual dedicado para criação de jogos 2D.
Recursos:
  • Handles de escala (arrastar bordas/cantos do objeto selecionado)
  • Inspector editável no painel esquerdo (posição, escala, física)
  • Zoom e panning da câmera
  • Undo / Redo
  • Vários tipos de objeto 2D
"""

import math
import pygame
import numpy as np
from collections import deque
from typing import List, Optional, Dict, Tuple

from engine.core import Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from engine.graphics.camera2d import Camera2D
import editor.theme as T
from editor.gui import GuiButton, SectionHeader


# ── Paleta de cores por tipo de objeto ──────────────────────────────────────
SHAPE_COLORS: Dict[str, Tuple[int,int,int]] = {
    "Quadrado":   (220,  80,  60),
    "Círculo":    (100, 180, 255),
    "Plataforma": ( 50, 150, 100),
    "Player":     ( 80, 200, 130),
    "Inimigo":    (210,  80, 200),
    "Trigger":    (240, 190,  40),
    "Mola":       ( 80, 180, 220),
}

# Handles: (nx, ny) em espaço normalizado do objeto — (-1,-1)=TL, (0,-1)=TC, (1,-1)=TR…
_HANDLE_OFFSETS = [
    (-1, -1), ( 0, -1), ( 1, -1),
    (-1,  0),            ( 1,  0),
    (-1,  1), ( 0,  1), ( 1,  1),
]
_HANDLE_SIZE = 8   # px (tamanho visual do handle em tela)
_HANDLE_HIT  = 12  # px (raio de clique, mais tolerante)


class Editor2DScene(Scene):
    # ──────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        self.game_objects:     List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index:   int              = -1

        # Câmera do editor 2D
        self.cam_obj = GameObject("EditorCamera")
        self.camera  = self.cam_obj.add_component(Camera2D(zoom=1.0))
        self.cam_obj.transform.position = np.array([400.0, 300.0, 0.0], dtype=np.float32)
        self._add_go(self.cam_obj)
        Camera2D.main = self.camera

        # Histórico de undo/redo 2D
        self._undo_stack: deque[list] = deque(maxlen=50)
        self._redo_stack: deque[list] = deque(maxlen=50)

        # Viewport
        self.grid_size = 32
        self.show_grid = True
        self.vp_left   = 240
        self.vp_top    = 30
        self.vp_right  = 1140
        self.vp_bottom = 740
        self.vp_w      = self.vp_right  - self.vp_left
        self.vp_h      = self.vp_bottom - self.vp_top

        # Play Mode
        self.playing        = False
        self.play_snapshot: Optional[list] = None

        # Drag de objetos
        self._dragging_target = None
        self._drag_offset     = np.zeros(3, dtype=np.float32)

        # Handles de escala
        # handle_idx: qual dos 8 handles está sendo arrastado (0-7 ou None)
        self._scale_handle_idx:  Optional[int]   = None
        self._scale_drag_origin: Optional[tuple] = None  # (mx, my) inicial
        self._scale_orig_pos:    Optional[np.ndarray] = None
        self._scale_orig_scale:  Optional[np.ndarray] = None

        # Panning (botão do meio)
        self._panning        = False
        self._pan_last_mouse = (0, 0)

        # Scroll da hierarquia
        self._hier_scroll = 0

        # Inspector: campo de foco para edição
        # "pos_x" | "pos_y" | "scale_x" | "scale_y" | "mass" | "gravity" | None
        self._focused_field: Optional[str] = None

        # Fontes
        self.font      = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_lg   = pygame.font.SysFont("monospace", 17, bold=True)
        self.font_sm   = pygame.font.SysFont("monospace", 11)

        # ── Botões toolbar ────────────────────────────────────────────
        _S  = T.BTN_SECONDARY; _SH = T.BTN_SECONDARY_HOVER
        _P  = T.BTN_PRIMARY;   _PH = T.BTN_PRIMARY_HOVER

        self.btn_back = GuiButton( 10,  4, 80, 22, "← Voltar",   on_click=self._go_back,     bg=_S, hover=_SH)
        self.btn_grid = GuiButton(100,  4, 80, 22, "Grade: ON",  on_click=self._toggle_grid, bg=_S, hover=_SH)
        self.btn_play = GuiButton( 10, 30,105, 26, "▶  PLAY",    on_click=self.toggle_play,  bg=T.BTN_SPECIAL, hover=T.BTN_SPECIAL_HOVER)
        self.btn_undo = GuiButton(120, 30, 55, 26, "↩ Undo",     on_click=self.undo,         bg=_S, hover=_SH)
        self.btn_redo = GuiButton(180, 30, 55, 26, "↪ Redo",     on_click=self.redo,         bg=_S, hover=_SH)

        # Botões Adicionar objeto
        self.shape_buttons = [
            GuiButton( 10, 106, 68, 24, "Quadrado",   on_click=lambda: self.spawn_object("Quadrado"),   bg=_P, hover=_PH),
            GuiButton( 82, 106, 68, 24, "Círculo",    on_click=lambda: self.spawn_object("Círculo"),    bg=_P, hover=_PH),
            GuiButton(154, 106, 76, 24, "Plataforma", on_click=lambda: self.spawn_object("Plataforma"), bg=_P, hover=_PH),
            GuiButton( 10, 134, 68, 24, "Player",     on_click=lambda: self.spawn_object("Player"),     bg=(30,100,60), hover=(40,130,80)),
            GuiButton( 82, 134, 68, 24, "Inimigo",    on_click=lambda: self.spawn_object("Inimigo"),    bg=(100,30,100), hover=(130,40,130)),
            GuiButton(154, 134, 76, 24, "Trigger",    on_click=lambda: self.spawn_object("Trigger"),    bg=(100,80,0), hover=(140,110,0)),
            GuiButton( 10, 162, 68, 24, "Mola",       on_click=lambda: self.spawn_object("Mola"),       bg=(20,80,100), hover=(30,110,140)),
            GuiButton( 82, 162, 75, 24, "✕ Excluir",  on_click=self.delete_selected,                    bg=T.BTN_DANGER, hover=T.BTN_DANGER_HOVER),
        ]

        self._all_toolbar_btns = [self.btn_back, self.btn_grid, self.btn_play,
                                   self.btn_undo, self.btn_redo] + self.shape_buttons

        self.spawn_default_scene()

    # ──────────────────────────────────────────────────────────────────────
    # Helpers de coordenada
    # ──────────────────────────────────────────────────────────────────────

    def _world_to_vp(self, world_pos: np.ndarray) -> Tuple[float, float]:
        if Camera2D.main is None:
            return float(world_pos[0]), float(world_pos[1])
        sx, sy = Camera2D.main.world_to_screen(world_pos, self.vp_w, self.vp_h)
        return sx + self.vp_left, sy + self.vp_top

    def _vp_to_world(self, mx: float, my: float) -> np.ndarray:
        if Camera2D.main is None:
            return np.array([mx, my, 0.0], dtype=np.float32)
        wx, wy = Camera2D.main.screen_to_world(
            (mx - self.vp_left, my - self.vp_top), self.vp_w, self.vp_h)
        return np.array([wx, wy, 0.0], dtype=np.float32)

    def _in_viewport(self, mx: float, my: float) -> bool:
        return self.vp_left < mx < self.vp_right and self.vp_top < my < self.vp_bottom

    def _zoom(self) -> float:
        return Camera2D.main.zoom if Camera2D.main else 1.0

    # ──────────────────────────────────────────────────────────────────────
    # Handles de escala
    # ──────────────────────────────────────────────────────────────────────

    def _handle_screen_pos(self, obj: GameObject, h_idx: int) -> Tuple[float, float]:
        """Posição de tela do handle h_idx para o objeto obj."""
        nx, ny = _HANDLE_OFFSETS[h_idx]
        pos   = obj.transform.position
        scale = obj.transform.scale
        zoom  = self._zoom()
        sx, sy = self._world_to_vp(pos)
        sw, sh = scale[0] * zoom, scale[1] * zoom
        return sx + nx * sw / 2, sy + ny * sh / 2

    def _hit_handle(self, obj: GameObject, mx: float, my: float) -> Optional[int]:
        """Retorna o índice do handle sob o cursor, ou None."""
        for i in range(8):
            hx, hy = self._handle_screen_pos(obj, i)
            if abs(mx - hx) <= _HANDLE_HIT / 2 and abs(my - hy) <= _HANDLE_HIT / 2:
                return i
        return None

    # ──────────────────────────────────────────────────────────────────────
    # Cena padrão
    # ──────────────────────────────────────────────────────────────────────

    def spawn_default_scene(self) -> None:
        floor = GameObject("Chão")
        floor.transform.position = np.array([400.0, 500.0, 0.0], dtype=np.float32)
        floor.transform.scale    = np.array([600.0,  32.0, 1.0], dtype=np.float32)
        floor.add_component(BoxCollider(width=600, height=32))
        rb = floor.add_component(RigidBody()); rb.is_kinematic = True
        floor.mesh_type = "Plataforma"
        self._add_go(floor); self.editable_objects.append(floor)

        player = GameObject("Player")
        player.transform.position = np.array([400.0, 200.0, 0.0], dtype=np.float32)
        player.transform.scale    = np.array([ 36.0,  48.0, 1.0], dtype=np.float32)
        player.add_component(BoxCollider(width=36, height=48))
        player.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        player.mesh_type = "Player"
        self._add_go(player); self.editable_objects.append(player)

        self.selected_index = 1

    # ──────────────────────────────────────────────────────────────────────
    # Gerenciamento de GameObjects
    # ──────────────────────────────────────────────────────────────────────

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
        name = f"{shape}_{len(self.editable_objects)}"
        go = GameObject(name)
        go.transform.position = center.copy()

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
        elif shape == "Player":
            go.transform.scale = np.array([36.0, 48.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=48))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape == "Inimigo":
            go.transform.scale = np.array([36.0, 36.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=36, height=36))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape == "Trigger":
            go.transform.scale = np.array([80.0, 80.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=80, height=80, is_trigger=True))
        elif shape == "Mola":
            go.transform.scale = np.array([40.0, 20.0, 1.0], dtype=np.float32)
            go.add_component(BoxCollider(width=40, height=20))
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

    # ──────────────────────────────────────────────────────────────────────
    # Snapshot 2D
    # ──────────────────────────────────────────────────────────────────────

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
        go.transform.position = np.array([pos[0], pos[1], 0.0], dtype=np.float32)
        go.transform.scale    = np.array([scale[0], scale[1], 1.0], dtype=np.float32)
        w, h = int(scale[0]), int(scale[1])
        if shape == "Quadrado":
            go.add_component(BoxCollider(width=w, height=h))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Círculo":
            go.add_component(CircleCollider(radius=max(1, w // 2)))
            go.add_component(RigidBody(mass=1.0))
        elif shape == "Plataforma":
            go.add_component(BoxCollider(width=w, height=h))
            rb = go.add_component(RigidBody()); rb.is_kinematic = True
        elif shape == "Player":
            go.add_component(BoxCollider(width=w, height=h))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape == "Inimigo":
            go.add_component(BoxCollider(width=w, height=h))
            go.add_component(RigidBody(mass=1.0, gravity_scale=1.0))
        elif shape == "Trigger":
            go.add_component(BoxCollider(width=w, height=h, is_trigger=True))
        elif shape == "Mola":
            go.add_component(BoxCollider(width=w, height=h))
            rb = go.add_component(RigidBody()); rb.is_kinematic = True
        go.mesh_type = shape
        self._add_go(go)
        self.editable_objects.append(go)
        return go

    # ──────────────────────────────────────────────────────────────────────
    # Play / Undo / Redo
    # ──────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────
    # Inspector — ajuste de propriedade com +/- delta
    # ──────────────────────────────────────────────────────────────────────

    def _adjust_prop(self, field: str, delta: float) -> None:
        """Incrementa/decrementa uma propriedade do objeto selecionado."""
        if self.playing or self.selected_index < 0:
            return
        obj = self.editable_objects[self.selected_index]
        rb  = obj.get_component(RigidBody)
        self._push2d()
        if field == "pos_x":
            obj.transform.position[0] += delta
        elif field == "pos_y":
            obj.transform.position[1] += delta
        elif field == "scale_x":
            obj.transform.scale[0] = max(4.0, obj.transform.scale[0] + delta)
        elif field == "scale_y":
            obj.transform.scale[1] = max(4.0, obj.transform.scale[1] + delta)
        elif field == "mass" and rb:
            rb.mass = max(0.1, round(rb.mass + delta, 2))
        elif field == "gravity" and rb:
            rb.gravity_scale = round(rb.gravity_scale + delta, 2)
        elif field == "kinematic" and rb:
            rb.is_kinematic = not rb.is_kinematic

    # ──────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self.playing:
            for go in self.game_objects:
                go.update(dt)
            BoxCollider.check_all()
            CircleCollider.check_all()

    # ──────────────────────────────────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        mx, my = pygame.mouse.get_pos()

        # ── Teclado ──────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.delete_selected()
            elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.undo()
            elif event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.redo()
            elif event.key == pygame.K_F1:
                self._toggle_grid()
            # Mover objeto com setas
            elif not self.playing and self.selected_index >= 0:
                step = 8.0
                obj  = self.editable_objects[self.selected_index]
                moved = False
                if event.key == pygame.K_LEFT:
                    obj.transform.position[0] -= step; moved = True
                elif event.key == pygame.K_RIGHT:
                    obj.transform.position[0] += step; moved = True
                elif event.key == pygame.K_UP:
                    obj.transform.position[1] -= step; moved = True
                elif event.key == pygame.K_DOWN:
                    obj.transform.position[1] += step; moved = True
                if moved:
                    self._push2d()

        # ── Scroll: zoom no viewport / hierarquia ───────────────────
        elif event.type == pygame.MOUSEWHEEL:
            if self._in_viewport(mx, my):
                factor = 1.1 if event.y > 0 else 0.9
                if Camera2D.main:
                    Camera2D.main.zoom = max(0.15, min(6.0, Camera2D.main.zoom * factor))
            elif mx < self.vp_left:
                max_sc = max(0, len(self.editable_objects) - 12)
                self._hier_scroll = max(0, min(max_sc, self._hier_scroll - event.y))

        # ── MOUSEBUTTONDOWN ─────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Botão do meio = panning
            if event.button == 2 and self._in_viewport(mx, my):
                self._panning        = True
                self._pan_last_mouse = (mx, my)
                return

            if event.button == 1:
                # Botões da UI
                for btn in self._all_toolbar_btns:
                    if btn.rect.collidepoint(mx, my):
                        btn.click()
                        return

                # Botões do inspector (direito)
                if mx >= self.vp_right:
                    self._handle_inspector_click(mx, my)
                    return

                # Clique na hierarquia (esquerda)
                if 8 < mx < 232:
                    ystart = 210
                    for i in range(self._hier_scroll, min(len(self.editable_objects), self._hier_scroll + 20)):
                        yp = ystart + (i - self._hier_scroll) * 22
                        if yp <= my < yp + 20:
                            self.selected_index = i
                            return

                # Viewport: verifica handles de escala primeiro
                if self._in_viewport(mx, my) and not self.playing:
                    if 0 <= self.selected_index < len(self.editable_objects):
                        obj = self.editable_objects[self.selected_index]
                        h   = self._hit_handle(obj, mx, my)
                        if h is not None:
                            self._scale_handle_idx  = h
                            self._scale_drag_origin = (mx, my)
                            self._scale_orig_pos    = obj.transform.position.copy()
                            self._scale_orig_scale  = obj.transform.scale.copy()
                            return

                # Hit-test no viewport
                if self._in_viewport(mx, my):
                    world_click = self._vp_to_world(mx, my)
                    clicked_any = False
                    for idx, obj in enumerate(self.editable_objects):
                        opos, oscale = obj.transform.position, obj.transform.scale
                        if obj.mesh_type == "Círculo":
                            hit = math.hypot(world_click[0]-opos[0], world_click[1]-opos[1]) <= oscale[0]/2
                        else:
                            hit = (abs(world_click[0]-opos[0]) <= oscale[0]/2 and
                                   abs(world_click[1]-opos[1]) <= oscale[1]/2)
                        if hit:
                            self.selected_index = idx
                            if not self.playing:
                                self._dragging_target = obj
                                self._drag_offset = (opos - world_click).copy()
                            clicked_any = True
                            break
                    if not clicked_any:
                        self.selected_index = -1

        # ── MOUSEMOTION ─────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            if self._panning and Camera2D.main:
                z  = Camera2D.main.zoom
                dx = (mx - self._pan_last_mouse[0]) / z
                dy = (my - self._pan_last_mouse[1]) / z
                Camera2D.main.transform.position[0] -= dx
                Camera2D.main.transform.position[1] -= dy
                self._pan_last_mouse = (mx, my)

            elif self._scale_handle_idx is not None and not self.playing:
                self._update_scale_handle(mx, my)

            elif self._dragging_target and not self.playing:
                world_pos = self._vp_to_world(mx, my)
                self._dragging_target.transform.position[0] = world_pos[0] + self._drag_offset[0]
                self._dragging_target.transform.position[1] = world_pos[1] + self._drag_offset[1]

        # ── MOUSEBUTTONUP ───────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self._panning = False
            if event.button == 1:
                if self._scale_handle_idx is not None:
                    self._scale_handle_idx  = None
                    self._scale_drag_origin = None
                    self._push2d()
                if self._dragging_target:
                    self._dragging_target = None
                    self._push2d()

    # ──────────────────────────────────────────────────────────────────────
    # Lógica dos handles de escala
    # ──────────────────────────────────────────────────────────────────────

    def _update_scale_handle(self, mx: float, my: float) -> None:
        if (self._scale_handle_idx is None or self._scale_drag_origin is None
                or self.selected_index < 0):
            return

        obj   = self.editable_objects[self.selected_index]
        zoom  = self._zoom()
        nx, ny = _HANDLE_OFFSETS[self._scale_handle_idx]

        # Delta em pixels de tela → mundo
        ddx = (mx - self._scale_drag_origin[0]) / zoom
        ddy = (my - self._scale_drag_origin[1]) / zoom

        orig_s = self._scale_orig_scale
        orig_p = self._scale_orig_pos

        # Determina qual eixo escalar e como mover a posição de ancoragem
        new_sw = orig_s[0]
        new_sh = orig_s[1]
        new_px = orig_p[0]
        new_py = orig_p[1]

        if nx != 0:   # mexe eixo X
            delta_w = ddx * nx * 2
            new_sw = max(4.0, orig_s[0] + delta_w)
            # o lado oposto fica fixo: posição se desloca na direção do handle
            new_px = orig_p[0] + (new_sw - orig_s[0]) / 2 * nx

        if ny != 0:   # mexe eixo Y
            delta_h = ddy * ny * 2
            new_sh = max(4.0, orig_s[1] + delta_h)
            new_py = orig_p[1] + (new_sh - orig_s[1]) / 2 * ny

        obj.transform.scale[0]    = new_sw
        obj.transform.scale[1]    = new_sh
        obj.transform.position[0] = new_px
        obj.transform.position[1] = new_py

    # ──────────────────────────────────────────────────────────────────────
    # Inspector click (painel direito)
    # ──────────────────────────────────────────────────────────────────────

    def _handle_inspector_click(self, mx: float, my: float) -> None:
        """Processa cliques nos botões +/- do inspector."""
        if self.selected_index < 0 or self.playing:
            return
        base_x = 1148
        fields  = self._inspector_fields()
        for i, (field, _label, _val) in enumerate(fields):
            fy    = 60 + i * 28
            delta = self._inspector_delta(field)
            if field == "kinematic":
                tog = pygame.Rect(base_x + 186, fy + 32, 46, 20)
                if tog.collidepoint(mx, my):
                    self._adjust_prop(field, 0.0)  # toggle ignora delta
            else:
                mr = pygame.Rect(base_x + 186, fy + 32, 22, 20)
                pr = pygame.Rect(base_x + 212, fy + 32, 22, 20)
                if mr.collidepoint(mx, my):
                    self._adjust_prop(field, -delta)
                elif pr.collidepoint(mx, my):
                    self._adjust_prop(field, +delta)

    def _inspector_fields(self) -> list:
        """Retorna lista de (field_id, label, valor_str) para o objeto selecionado."""
        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return []
        obj = self.editable_objects[self.selected_index]
        rb  = obj.get_component(RigidBody)
        fields = [
            ("pos_x",   "Pos X",  f"{obj.transform.position[0]:.1f}"),
            ("pos_y",   "Pos Y",  f"{obj.transform.position[1]:.1f}"),
            ("scale_x", "Larg.",  f"{obj.transform.scale[0]:.1f}"),
            ("scale_y", "Alt.",   f"{obj.transform.scale[1]:.1f}"),
        ]
        if rb:
            fields += [
                ("mass",      "Massa",  f"{rb.mass:.2f}"),
                ("gravity",   "Grav.",  f"{rb.gravity_scale:.2f}"),
                ("kinematic", "Cinemático", "Sim" if rb.is_kinematic else "Não"),
            ]
        return fields

    @staticmethod
    def _inspector_delta(field: str) -> float:
        if field in ("pos_x", "pos_y"):
            return 1.0
        if field in ("scale_x", "scale_y"):
            return 2.0
        if field == "mass":
            return 0.1
        if field == "gravity":
            return 0.1
        return 1.0

    # ──────────────────────────────────────────────────────────────────────
    # Draw
    # ──────────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(T.BG)
        self._draw_viewport(screen)
        self._draw_panel_left(screen)
        self._draw_panel_right(screen)
        self._draw_statusbar(screen)

    # ── Viewport ────────────────────────────────────────────────────────

    def _draw_viewport(self, screen: pygame.Surface) -> None:
        vp = pygame.Rect(self.vp_left, self.vp_top, self.vp_w, self.vp_h)
        pygame.draw.rect(screen, T.VIEWPORT_BG, vp)
        screen.set_clip(vp)

        zoom    = self._zoom()
        cam_pos = Camera2D.main.transform.position if Camera2D.main else np.zeros(3)

        # Grade
        if self.show_grid:
            gs    = max(6, int(self.grid_size * zoom))
            off_x = int(self.vp_left + self.vp_w/2 - cam_pos[0]*zoom) % gs
            off_y = int(self.vp_top  + self.vp_h/2 - cam_pos[1]*zoom) % gs
            gc    = T.alpha_blend(T.BORDER, 0.14)
            for x in range(self.vp_left + off_x - gs, self.vp_right + gs, gs):
                pygame.draw.line(screen, gc, (x, self.vp_top), (x, self.vp_bottom))
            for y in range(self.vp_top + off_y - gs, self.vp_bottom + gs, gs):
                pygame.draw.line(screen, gc, (self.vp_left, y), (self.vp_right, y))
            # Eixos de origem
            ox, oy = self._world_to_vp(np.zeros(3))
            if self.vp_left < ox < self.vp_right:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_Y, 0.5),
                                 (int(ox), self.vp_top), (int(ox), self.vp_bottom))
            if self.vp_top < oy < self.vp_bottom:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_X, 0.5),
                                 (self.vp_left, int(oy)), (self.vp_right, int(oy)))

        # Objetos
        for idx, obj in enumerate(self.editable_objects):
            self._draw_object(screen, obj, idx, zoom)

        # Handles de escala do objeto selecionado
        if (not self.playing and 0 <= self.selected_index < len(self.editable_objects)):
            self._draw_handles(screen, self.editable_objects[self.selected_index])

        screen.set_clip(None)
        pygame.draw.rect(screen, T.BORDER, vp, 2)

        # Overlay HUD
        zoom_lbl = self.font_sm.render(
            f"Zoom {zoom:.2f}x  |  Câmera ({cam_pos[0]:.0f}, {cam_pos[1]:.0f})"
            + ("  |  ● SIMULANDO" if self.playing else ""),
            True, T.VIEWPORT_LABEL if self.playing else T.TEXT_MUTED)
        screen.blit(zoom_lbl, (self.vp_left + 8, self.vp_top + 6))

    def _draw_object(self, screen: pygame.Surface, obj: GameObject, idx: int, zoom: float) -> None:
        pos   = obj.transform.position
        scale = obj.transform.scale
        sx, sy = self._world_to_vp(pos)
        sw, sh = scale[0]*zoom, scale[1]*zoom

        if sx+sw/2 < self.vp_left or sx-sw/2 > self.vp_right:
            return
        if sy+sh/2 < self.vp_top or sy-sh/2 > self.vp_bottom:
            return

        selected  = (idx == self.selected_index)
        base_col  = SHAPE_COLORS.get(obj.mesh_type, (160, 160, 160))
        fill_col  = T.ACCENT if selected else base_col
        is_trigger = False
        col = obj.get_component(BoxCollider) or obj.get_component(CircleCollider)
        if col and hasattr(col, "is_trigger"):
            is_trigger = col.is_trigger

        if obj.mesh_type == "Círculo":
            r = max(1, int(scale[0]/2*zoom))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*fill_col, 190), (r, r), r)
            border_c = T.ACCENT if selected else T.BORDER
            pygame.draw.circle(surf, (*border_c, 255), (r, r), r, 2)
            screen.blit(surf, (int(sx)-r, int(sy)-r))
        else:
            rect = pygame.Rect(int(sx-sw/2), int(sy-sh/2), int(sw), int(sh))
            surf = pygame.Surface((int(max(1, sw)), int(max(1, sh))), pygame.SRCALPHA)
            alpha = 120 if is_trigger else 190
            surf.fill((*fill_col, alpha))
            screen.blit(surf, rect.topleft)
            # Borda tracejada para trigger
            if is_trigger:
                for i in range(0, int(sw), 8):
                    pygame.draw.line(screen, (*T.WARNING, 200), (rect.left+i, rect.top), (min(rect.left+i+4, rect.right), rect.top))
                    pygame.draw.line(screen, (*T.WARNING, 200), (rect.left+i, rect.bottom), (min(rect.left+i+4, rect.right), rect.bottom))
            else:
                border_c = T.ACCENT if selected else T.BORDER
                pygame.draw.rect(screen, border_c, rect, 2, border_radius=4)

        # Nome sobre o objeto
        name_surf = self.font_sm.render(obj.name, True, T.TEXT_PRIMARY)
        screen.blit(name_surf, (int(sx)-name_surf.get_width()//2, int(sy-sh/2)-14))

    def _draw_handles(self, screen: pygame.Surface, obj: GameObject) -> None:
        """Desenha os 8 handles de escala ao redor do objeto selecionado."""
        zoom = self._zoom()
        for i, (nx, ny) in enumerate(_HANDLE_OFFSETS):
            hx, hy = self._handle_screen_pos(obj, i)
            if not (self.vp_left <= hx <= self.vp_right and self.vp_top <= hy <= self.vp_bottom):
                continue
            hr = _HANDLE_SIZE // 2
            # Cor por eixo (cantos=amarelo, bordas centrais=azul)
            is_corner = (nx != 0 and ny != 0)
            col = T.GIZMO_W if is_corner else T.ACCENT
            pygame.draw.rect(screen, T.BG, (int(hx)-hr-1, int(hy)-hr-1, _HANDLE_SIZE+2, _HANDLE_SIZE+2))
            pygame.draw.rect(screen, col,  (int(hx)-hr,   int(hy)-hr,   _HANDLE_SIZE,   _HANDLE_SIZE))

    # ── Painel Esquerdo ──────────────────────────────────────────────────

    def _draw_panel_left(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, T.PANEL, (0, 0, 240, 800))
        pygame.draw.line(screen, T.BORDER, (240, 0), (240, 800))

        # Título
        lbl = self.font_lg.render("EDITOR 2D", True, T.ACCENT)
        screen.blit(lbl, (10, 58))

        # Botões de controle
        for btn in [self.btn_back, self.btn_grid, self.btn_play, self.btn_undo, self.btn_redo]:
            btn.draw(screen, self.font_sm)

        # Adicionar objetos
        SectionHeader(10, 88, 220, "Adicionar Objeto").draw(screen, self.font_sm)
        for btn in self.shape_buttons:
            btn.draw(screen, self.font_sm)

        # Hierarquia
        SectionHeader(10, 192, 220, f"Hierarquia  [{len(self.editable_objects)} obj]").draw(screen, self.font_sm)
        ystart = 210
        visible = (720 - ystart) // 22
        for i in range(self._hier_scroll, min(len(self.editable_objects), self._hier_scroll + visible)):
            obj = self.editable_objects[i]
            yp  = ystart + (i - self._hier_scroll) * 22
            sel = (i == self.selected_index)
            if sel:
                pygame.draw.rect(screen, T.ACCENT_BG, (8, yp-1, 224, 20), border_radius=3)
            dot = SHAPE_COLORS.get(obj.mesh_type, T.TEXT_MUTED)
            pygame.draw.circle(screen, dot, (18, yp+8), 5)
            lbl = self.font.render(obj.name, True, T.TEXT_PRIMARY if sel else T.TEXT_MUTED)
            screen.blit(lbl, (28, yp))

    # ── Painel Direito (Inspector editável) ─────────────────────────────

    def _draw_panel_right(self, screen: pygame.Surface) -> None:
        base_x = 1148
        pygame.draw.rect(screen, T.PANEL, (1140, 0, 260, 800))
        pygame.draw.line(screen, T.BORDER, (1140, 0), (1140, 800))

        SectionHeader(base_x, 6, 232, "Inspector").draw(screen, self.font_sm)

        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            lbl = self.font.render("Nenhum objeto selecionado", True, T.TEXT_FAINT)
            screen.blit(lbl, (base_x, 30))
            return

        obj    = self.editable_objects[self.selected_index]
        fields = self._inspector_fields()
        dot    = SHAPE_COLORS.get(obj.mesh_type, (180,180,180))
        pygame.draw.rect(screen, dot, (base_x, 26, 12, 12), border_radius=2)
        name_s = self.font_bold.render(obj.name, True, T.TEXT_PRIMARY)
        screen.blit(name_s, (base_x+18, 26))
        type_s = self.font_sm.render(obj.mesh_type or "—", True, T.TEXT_MUTED)
        screen.blit(type_s, (base_x+18, 40))

        for i, (field, label, val_str) in enumerate(fields):
            fy = 60 + i * 28
            # Fundo alternado
            if i % 2 == 0:
                pygame.draw.rect(screen, T.SURFACE, (base_x, fy+28, 240, 28), border_radius=3)

            k_lbl = self.font_sm.render(label, True, T.TEXT_MUTED)
            screen.blit(k_lbl, (base_x+4, fy+34))

            v_lbl = self.font.render(val_str, True, T.TEXT_PRIMARY)
            screen.blit(v_lbl, (base_x+76, fy+34))

            if field != "kinematic" and not self.playing:
                # Botão −
                mr = pygame.Rect(base_x+186, fy+32, 22, 20)
                pygame.draw.rect(screen, T.BTN_SECONDARY, mr, border_radius=3)
                screen.blit(self.font_bold.render("−", True, T.TEXT_PRIMARY),
                            (mr.centerx - 5, mr.centery - 7))
                if mr.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, T.ACCENT_DIM, mr, 1, border_radius=3)

                # Botão +
                pr = pygame.Rect(base_x+212, fy+32, 22, 20)
                pygame.draw.rect(screen, T.BTN_SECONDARY, pr, border_radius=3)
                screen.blit(self.font_bold.render("+", True, T.TEXT_PRIMARY),
                            (pr.centerx - 5, pr.centery - 7))
                if pr.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, T.ACCENT_DIM, pr, 1, border_radius=3)
            elif field == "kinematic" and not self.playing:
                rb = obj.get_component(RigidBody)
                tog_r = pygame.Rect(base_x+186, fy+32, 46, 20)
                tog_col = T.SUCCESS if (rb and rb.is_kinematic) else T.BTN_SECONDARY
                pygame.draw.rect(screen, tog_col, tog_r, border_radius=10)
                tog_s = self.font_sm.render("Sim" if (rb and rb.is_kinematic) else "Não", True, T.TEXT_PRIMARY)
                screen.blit(tog_s, (tog_r.centerx - tog_s.get_width()//2, tog_r.centery - tog_s.get_height()//2))

        # Dica de handles
        if not self.playing:
            hint = self.font_sm.render("Arraste bordas do obj. p/ escalar", True, T.TEXT_FAINT)
            screen.blit(hint, (base_x, 60 + len(fields)*28 + 20))

        # Velocidade em jogo
        if self.playing:
            rb = obj.get_component(RigidBody)
            if rb:
                by = 60 + len(fields)*28 + 16
                v_lbl = self.font_sm.render("Velocidade em jogo:", True, T.TEXT_MUTED)
                screen.blit(v_lbl, (base_x, by))
                vx_l = self.font.render(f"Vx: {rb.velocity[0]:+.1f}", True, T.SUCCESS)
                vy_l = self.font.render(f"Vy: {rb.velocity[1]:+.1f}", True, T.WARNING)
                screen.blit(vx_l, (base_x, by+16))
                screen.blit(vy_l, (base_x+80, by+16))

    # ── Status Bar ───────────────────────────────────────────────────────

    def _draw_statusbar(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, T.PANEL, (240, 740, 900, 60))
        pygame.draw.line(screen, T.BORDER, (240, 740), (1140, 740))

        col = (80, 220, 100) if self.playing else T.TEXT_MUTED
        txt = "● SIMULANDO — física ativa" if self.playing else "○ Modo Edição"
        screen.blit(self.font_bold.render(txt, True, col), (260, 752))

        hints = "Del=Excluir  Ctrl+Z=Undo  Ctrl+Y=Redo  Scroll=Zoom  M.Meio=Pan  Setas=Mover  F1=Grade"
        screen.blit(self.font_sm.render(hints, True, T.TEXT_FAINT), (260, 768))
