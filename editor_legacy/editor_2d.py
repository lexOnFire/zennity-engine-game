from __future__ import annotations
"""
editor/editor_2d.py
───────────────────
Editor visual dedicado para criação de jogos 2D.

Recursos:
  • Handles de escala (arrastar bordas/cantos) com sync de collider
  • Inspector editável (+/-) com sync de collider
  • Layout dinâmico — adapta ao tamanho da janela
  • Undo/Redo com timing correto (push ANTES da mudança)
  • Notificações de status temporárias
  • Rename de objeto (double-click na hierarquia)
  • Duplicar objeto (Ctrl+D)
  • Aviso ao sair com alterações não salvas
  • Escala uniforme forçada para círculos
  • Auto-scroll da hierarquia ao selecionar
"""

import math
import time
import pygame
import numpy as np
from collections import deque
from typing import List, Optional, Dict, Tuple

from engine.core import Scene
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider
from engine.graphics.camera2d import Camera2D
import editor_legacy.theme as T
from editor_legacy.gui import GuiButton, SectionHeader


# ── Paleta de cores por tipo ─────────────────────────────────────────────────
SHAPE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "Quadrado":   (220,  80,  60),
    "Círculo":    (100, 180, 255),
    "Plataforma": ( 50, 150, 100),
    "Player":     ( 80, 200, 130),
    "Inimigo":    (210,  80, 200),
    "Trigger":    (240, 190,  40),
    "Mola":       ( 80, 180, 220),
}

# Handles: (nx, ny) normalizado (-1 a 1)
_HANDLE_OFFSETS = [
    (-1, -1), ( 0, -1), ( 1, -1),
    (-1,  0),            ( 1,  0),
    (-1,  1), ( 0,  1), ( 1,  1),
]
_HANDLE_SIZE = 8
_HANDLE_HIT  = 12


def _screen_size() -> Tuple[int, int]:
    surf = pygame.display.get_surface()
    return surf.get_size() if surf else (1280, 800)


class Editor2DScene(Scene):
    # ──────────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        self.game_objects:     List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index:   int              = -1

        # Câmera
        self.cam_obj = GameObject("EditorCamera")
        self.camera  = self.cam_obj.add_component(Camera2D(zoom=1.0))
        self.cam_obj.transform.position = np.array([400.0, 300.0, 0.0], dtype=np.float32)
        self._add_go(self.cam_obj)
        Camera2D.main = self.camera

        # Histórico
        self._undo_stack: deque[list] = deque(maxlen=50)
        self._redo_stack: deque[list] = deque(maxlen=50)

        # Configurações
        self.grid_size = 32
        self.show_grid = True

        # Play Mode
        self.playing        = False
        self.play_snapshot: Optional[list] = None

        # Drag de objetos — _push2d() é chamado no INÍCIO do drag (no BUTTONDOWN)
        self._dragging_target = None
        self._drag_offset     = np.zeros(3, dtype=np.float32)

        # Handles de escala
        self._scale_handle_idx:  Optional[int]        = None
        self._scale_drag_origin: Optional[Tuple]      = None
        self._scale_orig_pos:    Optional[np.ndarray] = None
        self._scale_orig_scale:  Optional[np.ndarray] = None
        self._scale_pushed       = False   # garante push único por drag

        # Panning
        self._panning        = False
        self._pan_last_mouse = (0, 0)

        # Hierarquia
        self._hier_scroll      = 0
        self._rename_index     = -1
        self._rename_text      = ""
        self._last_click_index = -1
        self._last_click_time  = 0.0

        # Notificações de status
        self._status_msg   = ""
        self._status_kind  = "info"   # "info" | "success" | "warning" | "error"
        self._status_until = 0.0

        # Diálogo de confirmação (voltar sem salvar)
        self._confirm_back = False

        # Fontes
        self.font      = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 13, bold=True)
        self.font_lg   = pygame.font.SysFont("monospace", 17, bold=True)
        self.font_sm   = pygame.font.SysFont("monospace", 11)

        # ── Botões ────────────────────────────────────────────────────────
        _S  = T.BTN_SECONDARY; _SH = T.BTN_SECONDARY_HOVER
        _P  = T.BTN_PRIMARY;   _PH = T.BTN_PRIMARY_HOVER

        self.btn_back = GuiButton( 10,  4, 80, 22, "← Voltar",   on_click=self._go_back,     bg=_S, hover=_SH)
        self.btn_grid = GuiButton(100,  4, 80, 22, "Grade: ON",  on_click=self._toggle_grid, bg=_S, hover=_SH)
        self.btn_play = GuiButton( 10, 30,105, 26, "▶  PLAY",    on_click=self.toggle_play,  bg=T.BTN_SPECIAL, hover=T.BTN_SPECIAL_HOVER)
        self.btn_undo = GuiButton(120, 30, 55, 26, "↩ Undo",     on_click=self.undo,         bg=_S, hover=_SH)
        self.btn_redo = GuiButton(180, 30, 55, 26, "↪ Redo",     on_click=self.redo,         bg=_S, hover=_SH)

        self.shape_buttons = [
            GuiButton( 10, 106, 68, 24, "Quadrado",   on_click=lambda: self.spawn_object("Quadrado"),   bg=_P, hover=_PH),
            GuiButton( 82, 106, 68, 24, "Círculo",    on_click=lambda: self.spawn_object("Círculo"),    bg=_P, hover=_PH),
            GuiButton(154, 106, 76, 24, "Plataforma", on_click=lambda: self.spawn_object("Plataforma"), bg=_P, hover=_PH),
            GuiButton( 10, 134, 68, 24, "Player",     on_click=lambda: self.spawn_object("Player"),     bg=(30,100,60),  hover=(40,130,80)),
            GuiButton( 82, 134, 68, 24, "Inimigo",    on_click=lambda: self.spawn_object("Inimigo"),    bg=(100,30,100), hover=(130,40,130)),
            GuiButton(154, 134, 76, 24, "Trigger",    on_click=lambda: self.spawn_object("Trigger"),    bg=(100,80,0),   hover=(140,110,0)),
            GuiButton( 10, 162, 68, 24, "Mola",       on_click=lambda: self.spawn_object("Mola"),       bg=(20,80,100),  hover=(30,110,140)),
            GuiButton( 82, 162, 68, 24, "✕ Excluir",  on_click=self.delete_selected,                    bg=T.BTN_DANGER, hover=T.BTN_DANGER_HOVER),
            GuiButton(154, 162, 76, 24, "Ctrl+D Dup", on_click=self.duplicate_selected,                 bg=_S, hover=_SH),
        ]

        self._all_toolbar_btns = [self.btn_back, self.btn_grid, self.btn_play,
                                   self.btn_undo, self.btn_redo] + self.shape_buttons

        self.spawn_default_scene()

    # ──────────────────────────────────────────────────────────────────────────
    # Layout dinâmico (adapta ao tamanho da janela)
    # ──────────────────────────────────────────────────────────────────────────

    def _layout(self) -> Dict[str, int]:
        sw, sh = _screen_size()
        LEFT   = 240
        RIGHT  = 260
        TOP    = 30
        BOTTOM = sh - 60          # 60px para a status bar
        return dict(
            sw=sw, sh=sh,
            vp_left=LEFT, vp_top=TOP,
            vp_right=sw - RIGHT, vp_bottom=BOTTOM,
            vp_w=sw - RIGHT - LEFT, vp_h=BOTTOM - TOP,
            panel_left_w=LEFT,
            panel_right_x=sw - RIGHT, panel_right_w=RIGHT,
            status_y=BOTTOM,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers de coordenada
    # ──────────────────────────────────────────────────────────────────────────

    def _world_to_vp(self, world_pos: np.ndarray, lay: Dict) -> Tuple[float, float]:
        if Camera2D.main is None:
            return float(world_pos[0]), float(world_pos[1])
        sx, sy = Camera2D.main.world_to_screen(world_pos, lay["vp_w"], lay["vp_h"])
        return sx + lay["vp_left"], sy + lay["vp_top"]

    def _vp_to_world(self, mx: float, my: float, lay: Dict) -> np.ndarray:
        if Camera2D.main is None:
            return np.array([mx, my, 0.0], dtype=np.float32)
        wx, wy = Camera2D.main.screen_to_world(
            (mx - lay["vp_left"], my - lay["vp_top"]), lay["vp_w"], lay["vp_h"])
        return np.array([wx, wy, 0.0], dtype=np.float32)

    def _in_viewport(self, mx: float, my: float, lay: Dict) -> bool:
        return lay["vp_left"] < mx < lay["vp_right"] and lay["vp_top"] < my < lay["vp_bottom"]

    def _zoom(self) -> float:
        return Camera2D.main.zoom if Camera2D.main else 1.0

    # ──────────────────────────────────────────────────────────────────────────
    # Notificações
    # ──────────────────────────────────────────────────────────────────────────

    def _notify(self, msg: str, kind: str = "info", duration: float = 2.5) -> None:
        self._status_msg   = msg
        self._status_kind  = kind
        self._status_until = time.time() + duration

    # ──────────────────────────────────────────────────────────────────────────
    # Handles de escala
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_screen_pos(self, obj: GameObject, h_idx: int, lay: Dict) -> Tuple[float, float]:
        nx, ny = _HANDLE_OFFSETS[h_idx]
        pos, scale, zoom = obj.transform.position, obj.transform.scale, self._zoom()
        sx, sy = self._world_to_vp(pos, lay)
        return sx + nx * scale[0] * zoom / 2, sy + ny * scale[1] * zoom / 2

    def _hit_handle(self, obj: GameObject, mx: float, my: float, lay: Dict) -> Optional[int]:
        for i in range(8):
            hx, hy = self._handle_screen_pos(obj, i, lay)
            if abs(mx - hx) <= _HANDLE_HIT / 2 and abs(my - hy) <= _HANDLE_HIT / 2:
                return i
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Sync de collider com scale
    # ──────────────────────────────────────────────────────────────────────────

    def _sync_collider(self, obj: GameObject) -> None:
        """Atualiza width/height/radius do collider para bater com o transform.scale."""
        scale = obj.transform.scale
        bc = obj.get_component(BoxCollider)
        if bc:
            bc.width  = max(1, int(scale[0]))
            bc.height = max(1, int(scale[1]))
            return
        cc = obj.get_component(CircleCollider)
        if cc:
            cc.radius = max(1, int(scale[0] / 2))

    # ──────────────────────────────────────────────────────────────────────────
    # Cena padrão
    # ──────────────────────────────────────────────────────────────────────────

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

    # ──────────────────────────────────────────────────────────────────────────
    # Gerenciamento de GameObjects
    # ──────────────────────────────────────────────────────────────────────────

    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        if go not in self.game_objects:
            self.game_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)
        if getattr(go, "scene", None) is self:
            go.destroy()

    def spawn_object(self, shape: str) -> None:
        if self.playing:
            return
        self._push2d()
        lay    = self._layout()
        center = self._vp_to_world(lay["vp_left"] + lay["vp_w"] / 2,
                                   lay["vp_top"]  + lay["vp_h"] / 2, lay)
        go = GameObject(f"{shape}_{len(self.editable_objects)}")
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
        self._scroll_to_selected()
        self._notify(f"'{shape}' criado", "success")

    def delete_selected(self) -> None:
        if self.playing or self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return
        name = self.editable_objects[self.selected_index].name
        self._push2d()
        obj = self.editable_objects.pop(self.selected_index)
        self._remove_go(obj)
        self.selected_index = max(0, self.selected_index - 1) if self.editable_objects else -1
        self._notify(f"'{name}' excluído", "warning")

    def duplicate_selected(self) -> None:
        """Ctrl+D — duplica o objeto selecionado."""
        if self.playing or self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            return
        src = self.editable_objects[self.selected_index]
        self._push2d()
        new_pos   = src.transform.position.copy()
        new_pos[0] += 20.0; new_pos[1] += 20.0
        go = self._create_obj(f"{src.name}_cópia", src.mesh_type,
                              new_pos, src.transform.scale.copy())
        self.selected_index = self.editable_objects.index(go)
        self._scroll_to_selected()
        self._notify(f"'{src.name}' duplicado", "success")

    # ──────────────────────────────────────────────────────────────────────────
    # Rename
    # ──────────────────────────────────────────────────────────────────────────

    def _start_rename(self, idx: int) -> None:
        self._rename_index = idx
        self._rename_text  = self.editable_objects[idx].name

    def _commit_rename(self) -> None:
        if self._rename_index >= 0 and self._rename_text.strip():
            self.editable_objects[self._rename_index].name = self._rename_text.strip()
            self._notify(f"Renomeado para '{self._rename_text.strip()}'", "info")
        self._rename_index = -1

    # ──────────────────────────────────────────────────────────────────────────
    # Snapshot 2D
    # ──────────────────────────────────────────────────────────────────────────

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
        self.selected_index = min(
            max(-1, self.selected_index), len(self.editable_objects) - 1)
        self._scroll_to_selected()

    def _push2d(self) -> None:
        self._undo_stack.append(self._snap2d())
        self._redo_stack.clear()

    def _create_obj(self, name: str, shape: str, pos: np.ndarray, scale: np.ndarray) -> GameObject:
        go = GameObject(name)
        go.transform.position = np.array([pos[0], pos[1], 0.0], dtype=np.float32)
        go.transform.scale    = np.array([scale[0], scale[1], 1.0], dtype=np.float32)
        w, h = max(1, int(scale[0])), max(1, int(scale[1]))
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

    # ──────────────────────────────────────────────────────────────────────────
    # Scroll da hierarquia
    # ──────────────────────────────────────────────────────────────────────────

    def _scroll_to_selected(self) -> None:
        """Ajusta _hier_scroll para garantir que selected_index esteja visível."""
        if self.selected_index < 0:
            return
        _VISIBLE = 12
        if self.selected_index < self._hier_scroll:
            self._hier_scroll = self.selected_index
        elif self.selected_index >= self._hier_scroll + _VISIBLE:
            self._hier_scroll = self.selected_index - _VISIBLE + 1

    # ──────────────────────────────────────────────────────────────────────────
    # Play / Undo / Redo
    # ──────────────────────────────────────────────────────────────────────────

    def undo(self) -> None:
        if self.playing or not self._undo_stack:
            return
        self._redo_stack.append(self._snap2d())
        self._restore2d(self._undo_stack.pop())
        self._notify("Desfazer", "info")

    def redo(self) -> None:
        if self.playing or not self._redo_stack:
            return
        self._undo_stack.append(self._snap2d())
        self._restore2d(self._redo_stack.pop())
        self._notify("Refazer", "info")

    def toggle_play(self) -> None:
        if not self.playing:
            self.play_snapshot = self._snap2d()
            self.playing = True
            self.btn_play.text        = "■  STOP"
            self.btn_play.bg_color    = T.BTN_DANGER
            self.btn_play.hover_color = T.BTN_DANGER_HOVER
            self._notify("Simulação iniciada", "success")
        else:
            self.playing = False
            self.btn_play.text        = "▶  PLAY"
            self.btn_play.bg_color    = T.BTN_SPECIAL
            self.btn_play.hover_color = T.BTN_SPECIAL_HOVER
            if self.play_snapshot is not None:
                self._restore2d(self.play_snapshot)
                self.play_snapshot = None
            self._notify("Simulação encerrada — cena restaurada", "info")

    def _go_back(self) -> None:
        if self._undo_stack:
            # Abre confirmação
            self._confirm_back = True
        else:
            self._do_back()

    def _do_back(self) -> None:
        if self.playing:
            self.toggle_play()
        from editor_legacy.launcher import LauncherScene
        if self.engine:
            self.engine.change_scene(LauncherScene())

    def _toggle_grid(self) -> None:
        self.show_grid = not self.show_grid
        self.btn_grid.text = "Grade: ON" if self.show_grid else "Grade: OFF"

    # ──────────────────────────────────────────────────────────────────────────
    # Inspector — ajuste de propriedade
    # ──────────────────────────────────────────────────────────────────────────

    def _adjust_prop(self, field: str, delta: float) -> None:
        if self.playing or self.selected_index < 0:
            return
        obj = self.editable_objects[self.selected_index]
        rb  = obj.get_component(RigidBody)
        changed = False

        if field == "pos_x":
            obj.transform.position[0] += delta; changed = True
        elif field == "pos_y":
            obj.transform.position[1] += delta; changed = True
        elif field == "scale_x":
            new_val = max(4.0, obj.transform.scale[0] + delta)
            # Círculo: escala uniforme
            if obj.mesh_type == "Círculo":
                new_val = max(4.0, obj.transform.scale[0] + delta)
                if abs(new_val - obj.transform.scale[0]) > 0.001:
                    obj.transform.scale[0] = new_val
                    obj.transform.scale[1] = new_val
                    self._sync_collider(obj); changed = True
            elif abs(new_val - obj.transform.scale[0]) > 0.001:
                obj.transform.scale[0] = new_val
                self._sync_collider(obj); changed = True
        elif field == "scale_y":
            if obj.mesh_type != "Círculo":
                new_val = max(4.0, obj.transform.scale[1] + delta)
                if abs(new_val - obj.transform.scale[1]) > 0.001:
                    obj.transform.scale[1] = new_val
                    self._sync_collider(obj); changed = True
        elif field == "mass" and rb:
            new_val = max(0.1, round(rb.mass + delta, 2))
            if abs(new_val - rb.mass) > 0.0001:
                rb.mass = new_val; changed = True
        elif field == "gravity" and rb:
            new_val = round(rb.gravity_scale + delta, 2)
            if abs(new_val - rb.gravity_scale) > 0.0001:
                rb.gravity_scale = new_val; changed = True
        elif field == "kinematic" and rb:
            rb.is_kinematic = not rb.is_kinematic; changed = True

        if changed:
            self._push2d()

    # ──────────────────────────────────────────────────────────────────────────
    # Scale handle logic
    # ──────────────────────────────────────────────────────────────────────────

    def _update_scale_handle(self, mx: float, my: float, lay: Dict) -> None:
        if self._scale_handle_idx is None or self.selected_index < 0:
            return
        obj  = self.editable_objects[self.selected_index]
        zoom = self._zoom()
        nx, ny = _HANDLE_OFFSETS[self._scale_handle_idx]
        ddx = (mx - self._scale_drag_origin[0]) / zoom
        ddy = (my - self._scale_drag_origin[1]) / zoom

        orig_s, orig_p = self._scale_orig_scale, self._scale_orig_pos
        new_sw, new_sh = orig_s[0], orig_s[1]
        new_px, new_py = orig_p[0], orig_p[1]

        if nx != 0:
            delta_w = ddx * nx * 2
            new_sw  = max(4.0, orig_s[0] + delta_w)
            new_px  = orig_p[0] + (new_sw - orig_s[0]) / 2 * nx
        if ny != 0:
            delta_h = ddy * ny * 2
            new_sh  = max(4.0, orig_s[1] + delta_h)
            new_py  = orig_p[1] + (new_sh - orig_s[1]) / 2 * ny

        # Círculo: mantém escala uniforme
        if obj.mesh_type == "Círculo":
            uniform = max(new_sw, new_sh)
            new_sw = new_sh = uniform

        obj.transform.scale[0]    = new_sw
        obj.transform.scale[1]    = new_sh
        obj.transform.position[0] = new_px
        obj.transform.position[1] = new_py
        self._sync_collider(obj)

    # ──────────────────────────────────────────────────────────────────────────
    # Inspector click
    # ──────────────────────────────────────────────────────────────────────────

    def _inspector_fields(self) -> list:
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
        if field in ("pos_x", "pos_y"):  return 1.0
        if field in ("scale_x", "scale_y"): return 2.0
        if field == "mass":    return 0.1
        if field == "gravity": return 0.1
        return 1.0

    def _handle_inspector_click(self, mx: float, my: float, lay: Dict) -> None:
        if self.selected_index < 0 or self.playing:
            return
        base_x  = lay["panel_right_x"] + 8
        fields   = self._inspector_fields()
        for i, (field, _label, _val) in enumerate(fields):
            fy    = 60 + i * 28
            delta = self._inspector_delta(field)
            if field == "kinematic":
                tog = pygame.Rect(base_x + 186, fy + 32, 46, 20)
                if tog.collidepoint(mx, my):
                    self._adjust_prop(field, 0.0)
            else:
                mr = pygame.Rect(base_x + 186, fy + 32, 22, 20)
                pr = pygame.Rect(base_x + 212, fy + 32, 22, 20)
                if mr.collidepoint(mx, my):
                    self._adjust_prop(field, -delta)
                elif pr.collidepoint(mx, my):
                    self._adjust_prop(field, +delta)

    # ──────────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self.playing:
            for go in self.game_objects:
                go.update(dt)
            BoxCollider.check_all()
            CircleCollider.check_all()

    # ──────────────────────────────────────────────────────────────────────────
    # Eventos
    # ──────────────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> None:
        mx, my = pygame.mouse.get_pos()
        lay    = self._layout()

        # ── Diálogo de confirmação de saída ────────────────────────────────
        if self._confirm_back:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_y:
                    self._confirm_back = False; self._do_back()
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_n:
                    self._confirm_back = False
            return

        # ── Rename em andamento ─────────────────────────────────────────────
        if self._rename_index >= 0:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._commit_rename()
                elif event.key == pygame.K_ESCAPE:
                    self._rename_index = -1
                elif event.key == pygame.K_BACKSPACE:
                    self._rename_text = self._rename_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self._rename_text += event.unicode
            return

        # ── Teclado ────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
            elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.delete_selected()
            elif event.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.undo()
            elif event.key == pygame.K_y and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.redo()
            elif event.key == pygame.K_d and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.duplicate_selected()
            elif event.key == pygame.K_F1:
                self._toggle_grid()
            elif not self.playing and self.selected_index >= 0:
                # Mover com setas — _push2d() ANTES de mover (FIX #9)
                step = 8.0
                obj  = self.editable_objects[self.selected_index]
                moved = False
                if event.key == pygame.K_LEFT:
                    self._push2d(); obj.transform.position[0] -= step; moved = True
                elif event.key == pygame.K_RIGHT:
                    self._push2d(); obj.transform.position[0] += step; moved = True
                elif event.key == pygame.K_UP:
                    self._push2d(); obj.transform.position[1] -= step; moved = True
                elif event.key == pygame.K_DOWN:
                    self._push2d(); obj.transform.position[1] += step; moved = True
                if moved:
                    self._notify(f"Posição: ({obj.transform.position[0]:.0f}, {obj.transform.position[1]:.0f})", "info", 1.0)

        # ── Scroll ─────────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEWHEEL:
            if self._in_viewport(mx, my, lay):
                factor = 1.1 if event.y > 0 else 0.9
                if Camera2D.main:
                    Camera2D.main.zoom = max(0.15, min(6.0, Camera2D.main.zoom * factor))
            elif mx < lay["vp_left"]:
                max_sc = max(0, len(self.editable_objects) - 12)
                self._hier_scroll = max(0, min(max_sc, self._hier_scroll - event.y))

        # ── MOUSEBUTTONDOWN ────────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 2 and self._in_viewport(mx, my, lay):
                self._panning = True; self._pan_last_mouse = (mx, my); return

            if event.button == 1:
                # Botões da UI
                for btn in self._all_toolbar_btns:
                    if btn.rect.collidepoint(mx, my):
                        btn.click(); return

                # Inspector (painel direito)
                if mx >= lay["panel_right_x"]:
                    self._handle_inspector_click(mx, my, lay); return

                # Hierarquia (painel esquerdo)
                if 8 < mx < 232:
                    ystart = 210
                    for i in range(self._hier_scroll,
                                   min(len(self.editable_objects), self._hier_scroll + 20)):
                        yp = ystart + (i - self._hier_scroll) * 22
                        if yp <= my < yp + 20:
                            now = time.time()
                            if i == self._last_click_index and (now - self._last_click_time) < 0.35:
                                self._start_rename(i)
                            else:
                                self.selected_index = i
                            self._last_click_index = i
                            self._last_click_time  = now
                            return

                # Handles de escala no viewport
                if self._in_viewport(mx, my, lay) and not self.playing:
                    if 0 <= self.selected_index < len(self.editable_objects):
                        obj = self.editable_objects[self.selected_index]
                        h   = self._hit_handle(obj, mx, my, lay)
                        if h is not None:
                            # _push2d() ANTES de começar a escalar (FIX #1/#2)
                            self._push2d()
                            self._scale_handle_idx  = h
                            self._scale_drag_origin = (mx, my)
                            self._scale_orig_pos    = obj.transform.position.copy()
                            self._scale_orig_scale  = obj.transform.scale.copy()
                            return

                # Hit-test no viewport (selecionar/arrastar)
                if self._in_viewport(mx, my, lay):
                    world_click = self._vp_to_world(mx, my, lay)
                    clicked_any = False
                    for idx, obj in enumerate(self.editable_objects):
                        opos, oscale = obj.transform.position, obj.transform.scale
                        if obj.mesh_type == "Círculo":
                            hit = math.hypot(world_click[0]-opos[0], world_click[1]-opos[1]) <= oscale[0]/2
                        else:
                            hit = (abs(world_click[0]-opos[0]) <= oscale[0]/2 and
                                   abs(world_click[1]-opos[1]) <= oscale[1]/2)
                        if hit:
                            if not self.playing:
                                # _push2d() ANTES de arrastar (FIX #1)
                                self._push2d()
                                self._dragging_target = obj
                                self._drag_offset = (opos - world_click).copy()
                            self.selected_index = idx
                            clicked_any = True
                            break
                    if not clicked_any:
                        self.selected_index = -1

        # ── MOUSEMOTION ────────────────────────────────────────────────────
        elif event.type == pygame.MOUSEMOTION:
            if self._panning and Camera2D.main:
                z  = Camera2D.main.zoom
                dx = (mx - self._pan_last_mouse[0]) / z
                dy = (my - self._pan_last_mouse[1]) / z
                Camera2D.main.transform.position[0] -= dx
                Camera2D.main.transform.position[1] -= dy
                self._pan_last_mouse = (mx, my)
            elif self._scale_handle_idx is not None and not self.playing:
                self._update_scale_handle(mx, my, lay)
            elif self._dragging_target and not self.playing:
                world_pos = self._vp_to_world(mx, my, lay)
                self._dragging_target.transform.position[0] = world_pos[0] + self._drag_offset[0]
                self._dragging_target.transform.position[1] = world_pos[1] + self._drag_offset[1]

        # ── MOUSEBUTTONUP ─────────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 2:
                self._panning = False
            if event.button == 1:
                # Não chama _push2d() aqui — já foi chamado no BUTTONDOWN (FIX #1/#2)
                self._scale_handle_idx  = None
                self._scale_drag_origin = None
                self._dragging_target   = None

    # ──────────────────────────────────────────────────────────────────────────
    # Draw
    # ──────────────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface) -> None:
        lay = self._layout()
        screen.fill(T.BG)
        self._draw_viewport(screen, lay)
        self._draw_panel_left(screen, lay)
        self._draw_panel_right(screen, lay)
        self._draw_statusbar(screen, lay)
        if self._confirm_back:
            self._draw_confirm_dialog(screen, lay)

    # ── Viewport ────────────────────────────────────────────────────────────

    def _draw_viewport(self, screen: pygame.Surface, lay: Dict) -> None:
        vp = pygame.Rect(lay["vp_left"], lay["vp_top"], lay["vp_w"], lay["vp_h"])
        pygame.draw.rect(screen, T.VIEWPORT_BG, vp)
        screen.set_clip(vp)

        zoom    = self._zoom()
        cam_pos = Camera2D.main.transform.position if Camera2D.main else np.zeros(3)

        # Grade
        if self.show_grid:
            gs    = max(6, int(self.grid_size * zoom))
            off_x = int(lay["vp_left"] + lay["vp_w"]/2 - cam_pos[0]*zoom) % gs
            off_y = int(lay["vp_top"]  + lay["vp_h"]/2 - cam_pos[1]*zoom) % gs
            gc    = T.alpha_blend(T.BORDER, 0.14)
            for x in range(lay["vp_left"] + off_x - gs, lay["vp_right"] + gs, gs):
                pygame.draw.line(screen, gc, (x, lay["vp_top"]), (x, lay["vp_bottom"]))
            for y in range(lay["vp_top"] + off_y - gs, lay["vp_bottom"] + gs, gs):
                pygame.draw.line(screen, gc, (lay["vp_left"], y), (lay["vp_right"], y))
            ox, oy = self._world_to_vp(np.zeros(3), lay)
            if lay["vp_left"] < ox < lay["vp_right"]:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_Y, 0.5),
                                 (int(ox), lay["vp_top"]), (int(ox), lay["vp_bottom"]))
            if lay["vp_top"] < oy < lay["vp_bottom"]:
                pygame.draw.line(screen, T.alpha_blend(T.GIZMO_X, 0.5),
                                 (lay["vp_left"], int(oy)), (lay["vp_right"], int(oy)))

        # Objetos
        for idx, obj in enumerate(self.editable_objects):
            self._draw_object(screen, obj, idx, zoom, lay)

        # Handles
        if (not self.playing and 0 <= self.selected_index < len(self.editable_objects)):
            self._draw_handles(screen, self.editable_objects[self.selected_index], lay)

        screen.set_clip(None)
        pygame.draw.rect(screen, T.BORDER, vp, 2)

        # HUD
        hud = f"Zoom {zoom:.2f}x  |  Cam ({cam_pos[0]:.0f}, {cam_pos[1]:.0f})"
        if self.playing: hud += "  |  ● SIMULANDO"
        lbl = self.font_sm.render(hud, True, T.VIEWPORT_LABEL if self.playing else T.TEXT_MUTED)
        screen.blit(lbl, (lay["vp_left"] + 8, lay["vp_top"] + 6))

    def _draw_object(self, screen, obj, idx, zoom, lay) -> None:
        pos, scale = obj.transform.position, obj.transform.scale
        sx, sy     = self._world_to_vp(pos, lay)
        sw, sh     = scale[0]*zoom, scale[1]*zoom

        if sx+sw/2 < lay["vp_left"] or sx-sw/2 > lay["vp_right"]: return
        if sy+sh/2 < lay["vp_top"]  or sy-sh/2 > lay["vp_bottom"]: return

        selected = (idx == self.selected_index)
        base_col = SHAPE_COLORS.get(obj.mesh_type, (160, 160, 160))
        fill_col = T.ACCENT if selected else base_col
        is_trigger = False
        col_bc = obj.get_component(BoxCollider) or obj.get_component(CircleCollider)
        if col_bc and hasattr(col_bc, "is_trigger"):
            is_trigger = col_bc.is_trigger

        if obj.mesh_type == "Círculo":
            r = max(1, int(scale[0]/2*zoom))
            surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*fill_col, 190), (r, r), r)
            pygame.draw.circle(surf, (*(T.ACCENT if selected else T.BORDER), 255), (r, r), r, 2)
            screen.blit(surf, (int(sx)-r, int(sy)-r))
        else:
            rect = pygame.Rect(int(sx-sw/2), int(sy-sh/2), max(1,int(sw)), max(1,int(sh)))
            surf = pygame.Surface((max(1,int(sw)), max(1,int(sh))), pygame.SRCALPHA)
            surf.fill((*fill_col, 120 if is_trigger else 190))
            screen.blit(surf, rect.topleft)
            if is_trigger:
                for i in range(0, int(sw), 8):
                    pygame.draw.line(screen, (*T.WARNING, 200),
                                     (rect.left+i, rect.top), (min(rect.left+i+4,rect.right), rect.top))
                    pygame.draw.line(screen, (*T.WARNING, 200),
                                     (rect.left+i, rect.bottom), (min(rect.left+i+4,rect.right), rect.bottom))
            else:
                pygame.draw.rect(screen, T.ACCENT if selected else T.BORDER, rect, 2, border_radius=4)

        name_s = self.font_sm.render(obj.name, True, T.TEXT_PRIMARY)
        screen.blit(name_s, (int(sx)-name_s.get_width()//2, int(sy-sh/2)-14))

    def _draw_handles(self, screen, obj, lay) -> None:
        zoom = self._zoom()
        for i, (nx, ny) in enumerate(_HANDLE_OFFSETS):
            hx, hy = self._handle_screen_pos(obj, i, lay)
            if not (lay["vp_left"] <= hx <= lay["vp_right"] and
                    lay["vp_top"]  <= hy <= lay["vp_bottom"]): continue
            hr  = _HANDLE_SIZE // 2
            col = T.GIZMO_W if (nx != 0 and ny != 0) else T.ACCENT
            # Circles: only corners (uniform) are active
            if obj.mesh_type == "Círculo" and not (nx != 0 and ny != 0):
                col = T.alpha_blend(col, 0.3)
            pygame.draw.rect(screen, T.BG,  (int(hx)-hr-1, int(hy)-hr-1, _HANDLE_SIZE+2, _HANDLE_SIZE+2))
            pygame.draw.rect(screen, col,   (int(hx)-hr,   int(hy)-hr,   _HANDLE_SIZE,   _HANDLE_SIZE))

    # ── Painel Esquerdo ────────────────────────────────────────────────────

    def _draw_panel_left(self, screen, lay) -> None:
        sh = lay["sh"]
        pygame.draw.rect(screen, T.PANEL, (0, 0, lay["panel_left_w"], sh))
        pygame.draw.line(screen, T.BORDER, (lay["panel_left_w"], 0), (lay["panel_left_w"], sh))

        lbl = self.font_lg.render("EDITOR 2D", True, T.ACCENT)
        screen.blit(lbl, (10, 58))

        for btn in [self.btn_back, self.btn_grid, self.btn_play, self.btn_undo, self.btn_redo]:
            btn.draw(screen, self.font_sm)
        SectionHeader(10, 88, 220, "Adicionar Objeto").draw(screen, self.font_sm)
        for btn in self.shape_buttons:
            btn.draw(screen, self.font_sm)

        # Hierarquia
        SectionHeader(10, 192, 220, f"Hierarquia [{len(self.editable_objects)} obj]").draw(screen, self.font_sm)
        ystart   = 210
        visible  = (lay["status_y"] - 20 - ystart) // 22
        for i in range(self._hier_scroll, min(len(self.editable_objects), self._hier_scroll + visible)):
            obj = self.editable_objects[i]
            yp  = ystart + (i - self._hier_scroll) * 22
            sel = (i == self.selected_index)
            # Rename ativo
            if self._rename_index == i:
                pygame.draw.rect(screen, T.SURFACE_2, (8, yp-1, 224, 20), border_radius=3)
                cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
                ren_s  = self.font.render(self._rename_text + cursor, True, T.ACCENT)
                screen.blit(ren_s, (28, yp))
            else:
                if sel:
                    pygame.draw.rect(screen, T.ACCENT_BG, (8, yp-1, 224, 20), border_radius=3)
                dot = SHAPE_COLORS.get(obj.mesh_type, T.TEXT_MUTED)
                pygame.draw.circle(screen, dot, (18, yp+8), 5)
                lbl = self.font.render(obj.name, True, T.TEXT_PRIMARY if sel else T.TEXT_MUTED)
                screen.blit(lbl, (28, yp))

    # ── Painel Direito ─────────────────────────────────────────────────────

    def _draw_panel_right(self, screen, lay) -> None:
        rx   = lay["panel_right_x"]
        bx   = rx + 8
        sh   = lay["sh"]
        pygame.draw.rect(screen, T.PANEL, (rx, 0, lay["panel_right_w"], sh))
        pygame.draw.line(screen, T.BORDER, (rx, 0), (rx, sh))

        SectionHeader(bx, 6, lay["panel_right_w"]-16, "Inspector").draw(screen, self.font_sm)

        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            screen.blit(self.font.render("Nenhum objeto selecionado", True, T.TEXT_FAINT), (bx, 30))
            return

        obj    = self.editable_objects[self.selected_index]
        fields = self._inspector_fields()
        dot    = SHAPE_COLORS.get(obj.mesh_type, (180,180,180))
        pygame.draw.rect(screen, dot, (bx, 26, 12, 12), border_radius=2)
        screen.blit(self.font_bold.render(obj.name, True, T.TEXT_PRIMARY), (bx+18, 26))
        screen.blit(self.font_sm.render(obj.mesh_type or "—", True, T.TEXT_MUTED), (bx+18, 40))

        for i, (field, label, val_str) in enumerate(fields):
            fy = 60 + i * 28
            if i % 2 == 0:
                pygame.draw.rect(screen, T.SURFACE, (bx, fy+28, lay["panel_right_w"]-16, 28), border_radius=3)
            screen.blit(self.font_sm.render(label, True, T.TEXT_MUTED),   (bx+4,  fy+34))
            screen.blit(self.font.render(val_str,  True, T.TEXT_PRIMARY), (bx+76, fy+34))

            if field != "kinematic" and not self.playing:
                mr = pygame.Rect(bx+186, fy+32, 22, 20)
                pr = pygame.Rect(bx+212, fy+32, 22, 20)
                for r, lbl_txt in ((mr, "−"), (pr, "+")):
                    pygame.draw.rect(screen, T.BTN_SECONDARY, r, border_radius=3)
                    screen.blit(self.font_bold.render(lbl_txt, True, T.TEXT_PRIMARY),
                                (r.centerx-5, r.centery-7))
                    if r.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen, T.ACCENT_DIM, r, 1, border_radius=3)
            elif field == "kinematic" and not self.playing:
                rb  = obj.get_component(RigidBody)
                kin = rb and rb.is_kinematic
                tog = pygame.Rect(bx+186, fy+32, 46, 20)
                pygame.draw.rect(screen, T.SUCCESS if kin else T.BTN_SECONDARY, tog, border_radius=10)
                ts  = self.font_sm.render("Sim" if kin else "Não", True, T.TEXT_PRIMARY)
                screen.blit(ts, (tog.centerx - ts.get_width()//2, tog.centery - ts.get_height()//2))

        # Dica
        hint_y = 60 + len(fields)*28 + 16
        screen.blit(self.font_sm.render("Arraste bordas p/ escalar", True, T.TEXT_FAINT), (bx, hint_y))
        screen.blit(self.font_sm.render("Duplo clique na lista = renomear", True, T.TEXT_FAINT), (bx, hint_y+14))

        # Velocidade em jogo
        if self.playing:
            rb = obj.get_component(RigidBody)
            if rb:
                by = hint_y + 36
                screen.blit(self.font_sm.render("Velocidade:", True, T.TEXT_MUTED), (bx, by))
                screen.blit(self.font.render(f"Vx: {rb.velocity[0]:+.1f}", True, T.SUCCESS), (bx, by+14))
                screen.blit(self.font.render(f"Vy: {rb.velocity[1]:+.1f}", True, T.WARNING), (bx+80, by+14))

    # ── Status Bar ─────────────────────────────────────────────────────────

    def _draw_statusbar(self, screen, lay) -> None:
        sy  = lay["status_y"]
        sw  = lay["sw"]
        sh  = lay["sh"]
        vl  = lay["vp_left"]
        vr  = lay["panel_right_x"]
        pygame.draw.rect(screen, T.PANEL, (vl, sy, vr - vl, sh - sy))
        pygame.draw.line(screen, T.BORDER, (vl, sy), (vr, sy))

        col = (80, 220, 100) if self.playing else T.TEXT_MUTED
        txt = "● SIMULANDO — física ativa" if self.playing else "○ Modo Edição"
        screen.blit(self.font_bold.render(txt, True, col), (vl + 10, sy + 6))

        # Notificação temporária
        if self._status_msg and time.time() < self._status_until:
            kind_col = {
                "info": T.TEXT_PRIMARY, "success": T.SUCCESS,
                "warning": T.WARNING,   "error": T.ERROR
            }.get(self._status_kind, T.TEXT_PRIMARY)
            n_surf = self.font.render(f"  ✦ {self._status_msg}", True, kind_col)
            screen.blit(n_surf, (vl + 10, sy + 22))
        else:
            hints = "Del=Excluir  Ctrl+Z/Y=Undo/Redo  Ctrl+D=Duplicar  Scroll=Zoom  M.Meio=Pan  ←↑↓→=Mover  F1=Grade"
            screen.blit(self.font_sm.render(hints, True, T.TEXT_FAINT), (vl + 10, sy + 26))

    # ── Diálogo de confirmação ─────────────────────────────────────────────

    def _draw_confirm_dialog(self, screen, lay) -> None:
        sw, sh = lay["sw"], lay["sh"]
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        mw, mh = 420, 130
        mx_d   = (sw - mw) // 2
        my_d   = (sh - mh) // 2
        pygame.draw.rect(screen, T.PANEL,  (mx_d, my_d, mw, mh), border_radius=8)
        pygame.draw.rect(screen, T.ACCENT, (mx_d, my_d, mw, mh), 2, border_radius=8)

        msg1 = self.font_bold.render("Sair sem salvar?", True, T.ACCENT)
        msg2 = self.font.render("As alterações serão perdidas.", True, T.TEXT_MUTED)
        msg3 = self.font.render("[Enter / Y] = Confirmar    [Esc / N] = Cancelar", True, T.TEXT_PRIMARY)
        screen.blit(msg1, (mx_d + 20, my_d + 16))
        screen.blit(msg2, (mx_d + 20, my_d + 40))
        screen.blit(msg3, (mx_d + 20, my_d + 70))
