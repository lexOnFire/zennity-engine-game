"""
Cena principal do editor 3D da Zennity Engine.
Melhorias nesta versão:
  - Undo/Redo (Ctrl+Z / Ctrl+Shift+Z)
  - PhysicsSim integrado com RigidBody3D da engine
  - MOUSEWHEEL correto (pygame.MOUSEWHEEL)
  - Snap de grade configurável (tecla G)
  - Barra de status mostra contagem do histórico
  - Scripts prontos (biblioteca builtin)
  - Templates de cena (Plataformer, Arremesso, Sandbox)
  - Sistema de Tags nos objetos
  - AudioManager integrado
  - Modos de câmera (Perspectiva, Top-Down, Side-Scroller)
  - Painel de boas-vindas para iniciantes
  - [v2] Sistema visual coeso — theme.py, GuiButton reformulado,
          tipografia com hierarquia, paleta dark profissional
  - [v3] Migrado para Layout — zero magic numbers em scene.py
  - [v4] Métodos de modal (_draw_welcome_modal, _draw_help_modal,
          _draw_templates_modal) implementados
  - [v5] handle_event implementado — corrige cliques do mouse
"""
from __future__ import annotations
import os
import json
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pygame

from engine.core import Scene
from engine.game_object import GameObject
from engine.assets import Assets
from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
from engine.graphics.math3d import project_vertices

from .gui import GuiButton, SectionHeader, Divider, Badge
from .mesh_factory import create_pyramid_mesh, create_sphere_mesh
from .camera_controller import OrbitCameraController
from .physics_sim import PhysicsSim
from .script_manager import ScriptManager
from .code_editor import CodeEditor
from .history import History
from . import theme as T
from .layout import (
    Layout,
    # constantes fixas (não mudam com resize)
    LEFT_PANEL_W, RIGHT_PANEL_W,
    TOP_BAR_H, STATUS_BAR_H,
    LEFT_PADDING, ROW_H, ROW_H_SMALL,
    BTN_W_THIRD, BTN_W_FULL,
    BTN_X_COL1, BTN_X_COL2, BTN_X_COL3,
    ADD_SECTION_Y, ADD_ROW1_Y, ADD_ROW2_Y, ADD_ROW3_Y,
    GIZMO_SECTION_Y, GIZMO_ROW_Y,
    SNAP_Y, TEMPLATES_Y,
    TREE_Y, TREE_ROW_H,
    INSPECTOR_PAD, INSPECTOR_W,
    INSP_HEADER_Y, INSP_PHYSICS_Y, INSP_SCRIPT_Y,
    INSP_COLOR_Y, INSP_CLONE_Y, INSP_HIER_Y, INSP_TAG_Y,
    INSP_TRANSFORM_Y,
)

_IDENTITY = np.eye(4, dtype=np.float32)

SNAP_SIZE = 0.5

_SHAPE_ICON = {
    "Cube":    "▣",
    "Pyramid": "△",
    "Sphere":  "○",
    "Plane":   "▬",
    "Capsule": "⬭",
    "Camera":  "◈",
    "Light":   "✦",
}

CAMERA_MODES = ["Perspectiva", "Top-Down", "Side-Scroller"]

CAMERA_MODE_PRESETS = {
    "Perspectiva":   {"yaw":  0.0, "pitch": 25.0, "dist": 6.0},
    "Top-Down":      {"yaw":  0.0, "pitch": 89.9, "dist": 8.0},
    "Side-Scroller": {"yaw": 90.0, "pitch":  5.0, "dist": 7.0},
}


def _point_in_polygon(x: float, y: float, poly: List[Tuple[int, int]]) -> bool:
    n = len(poly)
    if n < 3:
        return False
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xints:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


COLOR_PALETTE = [
    (220,  60,  60),   # vermelho
    (255, 140,   0),   # laranja
    (255, 220,  40),   # amarelo
    ( 60, 200,  80),   # verde
    ( 50, 130, 255),   # azul
    (160,  80, 220),   # roxo
    (255, 255, 255),   # branco
    (100, 100, 100),   # cinza
]

WELCOME_STEPS = [
    ("Bem-vindo ao Zennity Editor!",
     "Este é o editor 3D da Zennity Engine. Use os painéis laterais para criar e editar objetos na cena."),
    ("Adicionando Objetos",
     "No painel esquerdo, clique nos botões '+ Cubo', '+ Esfera' etc. para adicionar formas à cena."),
    ("Selecionando e Movendo",
     "Clique em um objeto na viewport ou na árvore para selecioná-lo. Use o gizmo para mover, girar ou escalar."),
    ("Câmera Orbital",
     "Segure o botão direito do mouse na viewport e arraste para orbitar. Scroll do mouse para zoom."),
    ("Play Mode",
     "Clique em PLAY para testar. Clique em STOP para voltar ao editor. Posições são restauradas."),
]

HELP_LINES = [
    "NAVEGAÇÃO",
    "  RMB + arrastar      Orbitar câmera",
    "  Scroll              Zoom in/out",
    "",
    "OBJETOS",
    "  Clique na viewport  Selecionar objeto",
    "  Shift + LMB drag   Mover objeto (XY)",
    "  X / Z ao mover     Travar eixo",
    "  Delete              Excluir selecionado",
    "  Ctrl+Z              Desfazer",
    "  Ctrl+Shift+Z        Refazer",
    "",
    "GIZMO",
    "  ⇔ Mover             Arrastar eixo colorido",
    "  ↻ Girar             Arrastar eixo para rotacionar",
    "  ⤢ Escala            Arrastar eixo para escalar",
    "",
    "OUTROS",
    "  Esc                 Fechar modal/editor",
    "  Double-click (árvore) Renomear objeto",
    "  G                   Grade snap on/off",
]


class EditorScene(Scene):

    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        self.font_title = self.font_body = self.font_btn = self.font_xyz = self.font_section = None

        self.camera_comp: Optional[Camera3D] = None
        self.camera_controller: Optional[OrbitCameraController] = None
        self.camera_mode_index: int = 0

        self.gizmo_mode: Optional[str] = "translate"
        self.is_dragging_gizmo = False
        self.active_gizmo_axis: Optional[str] = None
        self.gizmo_drag_last_mouse: Tuple[int, int] = (0, 0)
        self.gizmo_screen_points: Dict[str, Tuple[int, int]] = {}
        self.gizmo_screen_center: Optional[Tuple[int, int]] = None
        self.gizmo_ex = self.gizmo_ey = self.gizmo_ez = None

        self.is_dragging_object = False
        self.drag_object_last_mouse: Tuple[int, int] = (0, 0)
        self.click_start_pos: Optional[Tuple[int, int]] = None

        self.play_mode = False
        self.saved_scene_state: Optional[List[Dict[str, Any]]] = None

        self.light_angle: float = 45.0
        self.available_scripts: List[str] = ["Nenhum"]

        self.code_editor = CodeEditor()
        self.showing_help_modal = False
        self.showing_welcome    = True
        self.welcome_step       = 0

        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
        self._tree_scroll: int = 0
        self._inspector_scroll: int = 0
        self._rename_index: int = -1
        self._rename_text: str = ""
        self._rename_blink: float = 0.0
        self._rename_cursor_on: bool = True
        self._last_click_index: int = -1
        self._last_click_time: float = 0.0

        self.history = History()
        self.snap_enabled: bool = False
        self._tag_index: int = 0

        self._active_dropdown = None
        self._is_dragging_tree = False
        self._drag_tree_src = None

        # Notificação de status (feedback visual de ações)
        self._status_msg: str = ""
        self._status_timer: float = 0.0
        self._STATUS_DURATION = 2.5

        # Layout — inicializado com tamanho padrão; atualizado no update()
        self._lay = Layout(1280, 800)

    # -----------------------------------------------------------------------
    def _notify(self, msg: str, kind: str = "info") -> None:
        """Exibe mensagem temporária na status bar."""
        self._status_msg = msg
        self._status_timer = self._STATUS_DURATION
        self._status_kind = kind  # "info" | "success" | "error"

    def start(self) -> None:
        print("[EditorScene] Iniciando editor 3D...")
        # Tipografia com hierarquia clara
        self.font_title   = Assets.get_font(None, 13)   # seção labels (small caps)
        self.font_body    = Assets.get_font(None, 14)   # texto geral
        self.font_btn     = Assets.get_font(None, 13)   # botões
        self.font_xyz     = Assets.get_font(None, 15)   # valores numéricos
        self.font_section = Assets.get_font(None, 11)   # micro labels

        self.available_scripts = ScriptManager.list_scripts()

        lay = self._lay
        _P  = T.BTN_PRIMARY
        _PH = T.BTN_PRIMARY_HOVER

        # ── Painel esquerdo — Botões de formas ──────────────────────────────
        self.btn_add_cube    = GuiButton(BTN_X_COL1, ADD_ROW1_Y, BTN_W_THIRD, ROW_H, "+ Cubo",    _P, _PH)
        self.btn_add_pyramid = GuiButton(BTN_X_COL2, ADD_ROW1_Y, BTN_W_THIRD, ROW_H, "+ Pirâm",   _P, _PH)
        self.btn_add_sphere  = GuiButton(BTN_X_COL3, ADD_ROW1_Y, BTN_W_THIRD, ROW_H, "+ Esfera",  _P, _PH)
        self.btn_add_plane   = GuiButton(BTN_X_COL1, ADD_ROW2_Y, BTN_W_THIRD, ROW_H, "+ Plano",   _P, _PH)
        self.btn_add_capsule = GuiButton(BTN_X_COL2, ADD_ROW2_Y, BTN_W_THIRD, ROW_H, "+ Cápsula", _P, _PH)
        self.btn_add_camera  = GuiButton(BTN_X_COL3, ADD_ROW2_Y, BTN_W_THIRD, ROW_H, "+ Câmera",  _P, _PH)
        self.btn_add_light   = GuiButton(BTN_X_COL1, ADD_ROW3_Y, BTN_W_THIRD, ROW_H, "+ Luz",     _P, _PH)

        # ── Gizmo modes ─────────────────────────────────────────────────────
        _G = T.BTN_GIZMO; _GH = T.BTN_GIZMO_HOVER
        self.btn_mode_translate = GuiButton(BTN_X_COL1, GIZMO_ROW_Y, BTN_W_THIRD, ROW_H, "⇔ Mover",  _G, _GH)
        self.btn_mode_rotate    = GuiButton(BTN_X_COL2, GIZMO_ROW_Y, BTN_W_THIRD, ROW_H, "↻ Girar",  _G, _GH)
        self.btn_mode_scale     = GuiButton(BTN_X_COL3, GIZMO_ROW_Y, BTN_W_THIRD, ROW_H, "⤢ Escala", _G, _GH)

        # ── Snap + Templates ─────────────────────────────────────────────────
        _S = T.BTN_SECONDARY; _SH = T.BTN_SECONDARY_HOVER
        self.btn_snap      = GuiButton(LEFT_PADDING, SNAP_Y,      BTN_W_FULL, ROW_H_SMALL, "Grade: OFF", _S, _SH)
        self.btn_templates = GuiButton(LEFT_PADDING, TEMPLATES_Y, BTN_W_FULL, ROW_H_SMALL, "Templates",  T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)

        # ── Undo / Redo / Delete (posicionados no update()) ──────────────────
        self.btn_undo   = GuiButton(LEFT_PADDING,       lay.undo_y,   99,          ROW_H, "↩ Desfazer", _S, _SH)
        self.btn_redo   = GuiButton(LEFT_PADDING + 105, lay.redo_y,   99,          ROW_H, "↪ Refazer",  _S, _SH)
        self.btn_delete = GuiButton(LEFT_PADDING,       lay.delete_y, BTN_W_FULL,  ROW_H,
                                    "✕ Excluir Objeto", T.BTN_DANGER, T.BTN_DANGER_HOVER)

        # ── Scrollbar da árvore ──────────────────────────────────────────────
        self.btn_tree_up   = GuiButton(200, TREE_Y + 20,              26, 20, "▲", _S, _SH)
        self.btn_tree_down = GuiButton(200, TREE_Y + lay.tree_h - 2,  26, 20, "▼", _S, _SH)

        # ── Ângulo de luz ────────────────────────────────────────────────────
        self.btn_light_angle_dec = GuiButton(LEFT_PADDING,        lay.light_section_y, 38, ROW_H_SMALL, "<", _S, _SH)
        self.btn_light_angle_inc = GuiButton(LEFT_PANEL_W - 50,   lay.light_section_y, 38, ROW_H_SMALL, ">", _S, _SH)

        # ── Barra superior ───────────────────────────────────────────────────
        self.btn_menu_file   = GuiButton(110, 2, 52, 26, "File",   T.SURFACE, T.SURFACE_2)
        self.btn_menu_view   = GuiButton(166, 2, 52, 26, "View",   T.SURFACE, T.SURFACE_2)
        self.btn_menu_window = GuiButton(222, 2, 72, 26, "Window", T.SURFACE, T.SURFACE_2)

        # Botões legados fora de tela
        self.btn_new_scene   = GuiButton(-200, -200, 10, 10, "Novo")
        self.btn_save        = GuiButton(-200, -200, 10, 10, "Salvar")
        self.btn_load        = GuiButton(-200, -200, 10, 10, "Carregar")
        self.btn_camera_mode = GuiButton(-200, -200, 10, 10, "Camera")
        self.btn_welcome     = GuiButton(-200, -200, 10, 10, "Ajuda")

        self.btn_play_pause = GuiButton(lay.play_button_x, 3, 88, 25, "▶  PLAY",
                                        T.BTN_PRIMARY, T.BTN_PRIMARY_HOVER)

        # ── Inspector direito (posições calculadas via lay.inspector_x()) ────
        rx = lay.inspector_x()
        self.btn_toggle_static  = GuiButton(rx, INSP_PHYSICS_Y - 12, 20, 20, "", _S, _SH)
        self.btn_toggle_physics = GuiButton(rx, INSP_PHYSICS_Y + 18, 20, 20, "", _S, _SH)

        self.btn_vel_dec = GuiButton(rx,           INSP_PHYSICS_Y + 73, 38, 20, "−", _S, _SH)
        self.btn_vel_inc = GuiButton(rx + 145,     INSP_PHYSICS_Y + 73, 38, 20, "+", _S, _SH)

        self.btn_prev_script     = GuiButton(rx,                    INSP_SCRIPT_Y + 22, 28, 22, "<",  _S, _SH)
        self.btn_next_script     = GuiButton(lay.insp_btn_right(28),INSP_SCRIPT_Y + 22, 28, 22, ">",  _S, _SH)
        self.btn_new_script      = GuiButton(rx,                    INSP_SCRIPT_Y + 47, INSPECTOR_W, 20, "+ Novo Script",    _P, _PH)
        self.btn_edit_script     = GuiButton(rx,                    INSP_SCRIPT_Y + 70, 93,          20, "Editor Ext.",      T.BTN_CODE, T.BTN_CODE_HOVER)
        self.btn_internal_editor = GuiButton(rx + 110,              INSP_SCRIPT_Y + 70, 84,          20, "Editor Int.",      T.BTN_CODE, T.BTN_CODE_HOVER)
        self.btn_script_help     = GuiButton(rx,                    INSP_SCRIPT_Y + 93, INSPECTOR_W, 20, "Guia de Comandos", T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)

        self.btn_clone      = GuiButton(rx,                    INSP_CLONE_Y, INSPECTOR_W, ROW_H, "⧉ Clonar Objeto", T.BTN_SPECIAL, T.BTN_SPECIAL_HOVER)
        self.btn_prev_parent= GuiButton(rx,                    INSP_HIER_Y + 3, 28, 22, "<", _S, _SH)
        self.btn_next_parent= GuiButton(lay.insp_btn_right(28),INSP_HIER_Y + 3, 28, 22, ">", _S, _SH)
        self.btn_prev_tag   = GuiButton(rx,                    INSP_TAG_Y  + 3, 28, 22, "<", _S, _SH)
        self.btn_next_tag   = GuiButton(lay.insp_btn_right(28),INSP_TAG_Y  + 3, 28, 22, ">", _S, _SH)

        self.btn_colors = [
            GuiButton(lay.insp_color_btn_x(i), INSP_COLOR_Y + 24, 26, 26, "",
                      bg_color=c, hover_color=c)
            for i, c in enumerate(COLOR_PALETTE)
        ]

        # ── Templates modal ──────────────────────────────────────────────────
        self.showing_templates  = False
        self._template_list     = self._load_template_list()
        self.btn_template_items = []
        for i, tpl in enumerate(self._template_list):
            self.btn_template_items.append(
                GuiButton(280, 120 + i * 60, 440, 48,
                          tpl.get("_template_name", f"Template {i+1}"),
                          T.SURFACE, T.SURFACE_2)
            )
        self.btn_templates_close = GuiButton(660, 80, 80, 28, "Fechar",
                                             T.BTN_DANGER, T.BTN_DANGER_HOVER)

        # ── Botões do modal de boas-vindas ───────────────────────────────────
        self.btn_welcome_next  = GuiButton(560, 340, 110, 30, "Próximo →",
                                           T.BTN_PRIMARY, T.BTN_PRIMARY_HOVER)
        self.btn_welcome_prev  = GuiButton(330, 340, 110, 30, "← Anterior",
                                           T.BTN_SECONDARY, T.BTN_SECONDARY_HOVER)
        self.btn_welcome_close = GuiButton(445, 340, 110, 30, "Fechar",
                                           T.BTN_DANGER, T.BTN_DANGER_HOVER)

        # ── Câmera ───────────────────────────────────────────────────────────
        cam_obj = GameObject("EditorCamera")
        vx, vy, vw, vh = lay.viewport_camera_params(play_mode=False)
        self.camera_comp = cam_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=vx, viewport_y=vy,
            viewport_width=vw, viewport_height=vh,
        ))
        self.camera_controller = cam_obj.add_component(OrbitCameraController())
        self._add_go(cam_obj)
        self.spawn_object("Cube")

    # -----------------------------------------------------------------------
    def _load_template_list(self) -> List[Dict]:
        templates = []
        demos_dir = os.path.join(os.path.dirname(__file__), "..", "demos")
        for fname in sorted(os.listdir(demos_dir)):
            if fname.startswith("template_") and fname.endswith(".json"):
                try:
                    with open(os.path.join(demos_dir, fname)) as f:
                        data = json.load(f)
                    if "_template_name" not in data:
                        data["_template_name"] = fname.replace("template_", "").replace(".json", "").capitalize()
                    templates.append(data)
                except Exception:
                    pass
        return templates

    def _load_template(self, tpl: Dict) -> None:
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        self.selected_index = -1
        objects_data = tpl.get("objects", [])
        for obj_data in objects_data:
            shape = obj_data.get("shape", "Cube")
            color = tuple(obj_data.get("color", [180, 180, 180]))
            go = self._make_mesh(shape, color)
            pos = obj_data.get("position", [0, 0, 0])
            rot = obj_data.get("rotation", [0, 0, 0])
            sc  = obj_data.get("scale",    [1, 1, 1])
            go.transform.position = np.array(pos, np.float32)
            go.transform.rotation = np.array(rot, np.float32)
            go.transform.scale    = np.array(sc,  np.float32)
            go.name = obj_data.get("name", shape)
            self._add_go(go)
            self.editable_objects.append(go)

    def _set_camera_mode(self, mode_name: str) -> None:
        preset = CAMERA_MODE_PRESETS.get(mode_name, CAMERA_MODE_PRESETS["Perspectiva"])
        self.camera_controller.target_yaw   = preset["yaw"]
        self.camera_controller.target_pitch = preset["pitch"]
        self.camera_controller.target_distance = preset["dist"]

    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def _snap(self, v: np.ndarray) -> np.ndarray:
        if self.snap_enabled:
            return np.round(v / SNAP_SIZE) * SNAP_SIZE
        return v

    def _make_mesh(self, shape: str, color: tuple):
        go = GameObject(shape)
        go.mesh_type = shape
        if shape == "Cube":
            mesh = Assets.create_cube_mesh(1.0)
        elif shape == "Pyramid":
            mesh = create_pyramid_mesh()
        elif shape == "Sphere":
            mesh = create_sphere_mesh()
        elif shape == "Plane":
            mesh = Assets.create_cube_mesh(1.0)
            go.transform.scale = np.array([2.0, 0.05, 2.0], np.float32)
        elif shape == "Capsule":
            mesh = create_sphere_mesh()
            go.transform.scale = np.array([1.0, 1.8, 1.0], np.float32)
        elif shape in ("Camera", "Light"):
            mesh = Assets.create_cube_mesh(0.3)
        else:
            mesh = Assets.create_cube_mesh(1.0)
        go.add_component(MeshRenderer3D(mesh, color=color, wireframe=False))
        return go

    def spawn_object(self, shape: str) -> None:
        counts = {
            "Cube": "cube_count", "Pyramid": "pyramid_count",
            "Sphere": "sphere_count", "Plane": "plane_count",
            "Capsule": "capsule_count", "Camera": "camera_count", "Light": "light_count",
        }
        attr = counts.get(shape, "cube_count")
        setattr(self, attr, getattr(self, attr) + 1)
        n = getattr(self, attr)

        colors = {
            "Cube":    (180, 180, 220),
            "Pyramid": (220, 180, 100),
            "Sphere":  (100, 200, 180),
            "Plane":   (120, 160, 120),
            "Capsule": (200, 140, 180),
            "Camera":  (200, 200,  80),
            "Light":   (255, 240, 140),
        }
        color = colors.get(shape, (180, 180, 180))
        go = self._make_mesh(shape, color)
        go.name = f"{shape}{n}"

        # Offset determinístico baseado no índice de spawn para evitar sobreposição
        offset_x = (n % 5 - 2) * 0.4
        offset_z = (n // 5) * 0.4
        go.transform.position = np.array([offset_x, 0.0, 2.0 + offset_z], np.float32)

        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._notify(f"{go.name} adicionado", "success")

    def delete_selected(self) -> None:
        if 0 <= self.selected_index < len(self.editable_objects):
            obj = self.editable_objects.pop(self.selected_index)
            self._remove_go(obj)
            self.selected_index = min(self.selected_index, len(self.editable_objects) - 1) if self.editable_objects else -1
            self._notify(f"{obj.name} removido", "info")

    def clone_selected(self) -> None:
        if 0 <= self.selected_index < len(self.editable_objects):
            src = self.editable_objects[self.selected_index]
            r = src.get_component(MeshRenderer3D)
            color = r.color if r else (180, 180, 180)
            shape = src.name.rstrip("0123456789")
            go = self._make_mesh(shape, color)
            go.name = src.name + "_clone"
            go.transform.position = src.transform.position.copy() + np.array([0.5, 0.0, 0.0], np.float32)
            go.transform.rotation = src.transform.rotation.copy()
            go.transform.scale    = src.transform.scale.copy()
            self._add_go(go)
            self.editable_objects.append(go)
            self.selected_index = len(self.editable_objects) - 1
            self._notify(f"{go.name} clonado", "success")

    def _build_flat_tree(self) -> List[Tuple[GameObject, int]]:
        result = []
        def traverse(obj, depth):
            result.append((obj, depth))
            for child in self.editable_objects:
                if getattr(child, "parent", None) is obj:
                    traverse(child, depth + 1)
        for obj in self.editable_objects:
            if getattr(obj, "parent", None) is None:
                traverse(obj, 0)
        return result

    def _start_rename(self, idx: int) -> None:
        self._rename_index = idx
        self._rename_text  = self.editable_objects[idx].name
        self._rename_blink = 0.0

    def _commit_rename(self) -> None:
        if self._rename_index >= 0 and self._rename_text.strip():
            self.editable_objects[self._rename_index].name = self._rename_text.strip()
        self._rename_index = -1
        self._rename_text  = ""

    def _cancel_rename(self) -> None:
        self._rename_index = -1
        self._rename_text  = ""

    def _tree_scroll_to(self, idx: int) -> None:
        lay = self._lay
        visible_rows = lay.tree_h // TREE_ROW_H
        if idx < self._tree_scroll:
            self._tree_scroll = idx
        elif idx >= self._tree_scroll + visible_rows:
            self._tree_scroll = idx - visible_rows + 1

    def _max_scroll(self) -> int:
        lay = self._lay
        visible_rows = lay.tree_h // TREE_ROW_H
        return max(0, len(self.editable_objects) - visible_rows)

    def save_scene(self) -> None:
        data = {"objects": []}
        for obj in self.editable_objects:
            r = obj.get_component(MeshRenderer3D)
            color = list(r.color) if r else [180, 180, 180]
            shape = obj.name.rstrip("0123456789").replace("_clone", "")
            data["objects"].append({
                "name":     obj.name,
                "shape":    shape,
                "color":    color,
                "position": obj.transform.position.tolist(),
                "rotation": obj.transform.rotation.tolist(),
                "scale":    obj.transform.scale.tolist(),
            })
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self._notify("Cena salva em demos/scene.json", "success")

    def load_scene(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        if not os.path.exists(path):
            self._notify("scene.json não encontrado", "error")
            return
        with open(path) as f:
            data = json.load(f)
        for obj in list(self.editable_objects):
            self._remove_go(obj)
        self.editable_objects.clear()
        self.selected_index = -1
        for obj_data in data.get("objects", []):
            shape = obj_data.get("shape", "Cube")
            color = tuple(obj_data.get("color", [180, 180, 180]))
            go = self._make_mesh(shape, color)
            go.transform.position = np.array(obj_data.get("position", [0, 0, 0]), np.float32)
            go.transform.rotation = np.array(obj_data.get("rotation", [0, 0, 0]), np.float32)
            go.transform.scale    = np.array(obj_data.get("scale",    [1, 1, 1]), np.float32)
            go.name = obj_data.get("name", shape)
            self._add_go(go)
            self.editable_objects.append(go)
        self._notify("Cena carregada", "success")

    def _select_at(self, mx: int, my: int) -> None:
        best_idx, best_depth = -1, float("inf")
        for idx, obj in enumerate(self.editable_objects):
            r = obj.get_component(MeshRenderer3D)
            if r and r.last_screen_coords is not None:
                for face in r.mesh.faces:
                    poly = [tuple(r.last_screen_coords[vi]) for vi in face]
                    if _point_in_polygon(mx, my, poly):
                        cam_z = -(self.camera_comp.view_matrix @ np.append(obj.transform.position, 1.0))[2]
                        if cam_z < best_depth:
                            best_depth, best_idx = cam_z, idx
        if best_idx != -1:
            self.selected_index = best_idx

    # -----------------------------------------------------------------------
    def _draw_floor_grid(self, screen: pygame.Surface) -> None:
        verts = []
        for x in range(-5, 6): verts += [[x, -0.5, -5.0], [x, -0.5, 5.0]]
        for z in range(-5, 6): verts += [[-5.0, -0.5, z], [5.0, -0.5, z]]
        verts = np.array(verts, np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x, self.camera_comp.viewport_y
        sx = vx + (ndc[:, 0] + 1) * vw / 2
        sy = vy + (-ndc[:, 1] + 1) * vh / 2
        near = self.camera_comp.near
        for i in range(0, len(verts), 2):
            if depths[i] > near and depths[i + 1] > near:
                p0 = (int(sx[i]),   int(sy[i]))
                p1 = (int(sx[i+1]), int(sy[i+1]))
                center = (
                    (abs(verts[i][0]) < 0.01 and abs(verts[i][2] - verts[i+1][2]) > 0.01) or
                    (abs(verts[i][2]) < 0.01 and abs(verts[i][0] - verts[i+1][0]) > 0.01)
                )
                pygame.draw.line(screen, T.grid_color(center), p0, p1, 2 if center else 1)

    # -----------------------------------------------------------------------
    def _reposition_buttons(self) -> None:
        """Reposiciona todos os botões cujos X/Y dependem do tamanho da janela."""
        lay = self._lay
        rx  = lay.inspector_x()

        # Inspector esquerda
        self.btn_toggle_static.x  = rx
        self.btn_toggle_physics.x = rx
        self.btn_vel_dec.x        = rx
        self.btn_vel_inc.x        = rx + 145
        self.btn_prev_script.x    = rx
        self.btn_next_script.x    = lay.insp_btn_right(28)
        self.btn_new_script.x     = rx
        self.btn_edit_script.x    = rx
        self.btn_internal_editor.x = rx + 110
        self.btn_script_help.x    = rx
        self.btn_clone.x          = rx
        self.btn_prev_parent.x    = rx
        self.btn_next_parent.x    = lay.insp_btn_right(28)
        self.btn_prev_tag.x       = rx
        self.btn_next_tag.x       = lay.insp_btn_right(28)
        for i, btn in enumerate(self.btn_colors):
            btn.x = lay.insp_color_btn_x(i)

        # PLAY
        self.btn_play_pause.x = lay.play_button_x

        # Botões abaixo da árvore
        self.btn_tree_down.y       = TREE_Y + lay.tree_h - 2
        self.btn_undo.y            = lay.undo_y
        self.btn_redo.y            = lay.redo_y
        self.btn_delete.y          = lay.delete_y
        self.btn_light_angle_dec.y = lay.light_section_y
        self.btn_light_angle_inc.y = lay.light_section_y
        self.btn_light_angle_inc.x = LEFT_PANEL_W - 50

        # Scroll da árvore
        self.btn_tree_up.x         = LEFT_PANEL_W - 30
        self.btn_tree_down.x       = LEFT_PANEL_W - 30

        # Reposiciona botões do modal de boas-vindas (centraliza na tela)
        sw = lay.screen_w
        sh = lay.screen_h
        mw, mh = 500, 200
        mx_ = (sw - mw) // 2
        my_ = (sh - mh) // 2
        btn_y = my_ + mh - 46
        self.btn_welcome_prev.x  = mx_ + 10
        self.btn_welcome_prev.y  = btn_y
        self.btn_welcome_close.x = mx_ + (mw - 110) // 2
        self.btn_welcome_close.y = btn_y
        self.btn_welcome_next.x  = mx_ + mw - 120
        self.btn_welcome_next.y  = btn_y

        # Reposiciona botões do modal de templates
        mw_t, mh_t = 500, 360
        mx_t = (sw - mw_t) // 2
        my_t = (sh - mh_t) // 2
        close_w, close_h = 100, 26
        self.btn_templates_close.x = mx_t + (mw_t - close_w) // 2
        self.btn_templates_close.y = my_t + mh_t - close_h - 10
        self.btn_templates_close.w = close_w

    # -----------------------------------------------------------------------
    def update(self, dt: float) -> None:
        # Status timer
        if self._status_timer > 0:
            self._status_timer -= dt

        screen_surf = pygame.display.get_surface()
        if screen_surf:
            w, h = screen_surf.get_size()
            self._lay.update(w, h)
            lay = self._lay

            # Câmera
            vx, vy, vw, vh = lay.viewport_camera_params(self.play_mode)
            self.camera_comp.viewport_x      = vx
            self.camera_comp.viewport_y      = vy
            self.camera_comp.viewport_width  = vw
            self.camera_comp.viewport_height = vh

            self._reposition_buttons()

        if self.play_mode:
            for obj in self.editable_objects:
                ScriptManager.update(obj, dt)
            PhysicsSim.step(self.editable_objects, dt)
        elif self.is_dragging_gizmo and 0 <= self.selected_index < len(self.editable_objects):
            sel = self.editable_objects[self.selected_index]
            mp  = pygame.mouse.get_pos()
            dx  = mp[0] - self.gizmo_drag_last_mouse[0]
            dy  = mp[1] - self.gizmo_drag_last_mouse[1]
            self.gizmo_drag_last_mouse = mp
            if self.gizmo_mode == "translate":
                if   self.active_gizmo_axis == 'x': sel.transform.position[0] += dx * 0.015
                elif self.active_gizmo_axis == 'y': sel.transform.position[1] -= dy * 0.015
                elif self.active_gizmo_axis == 'z': sel.transform.position[2] -= dy * 0.015
                sel.transform.position = self._snap(sel.transform.position)
            elif self.gizmo_mode == "scale":
                if   self.active_gizmo_axis == 'x': sel.transform.scale[0] = max(0.1, sel.transform.scale[0] + dx * 0.015)
                elif self.active_gizmo_axis == 'y': sel.transform.scale[1] = max(0.1, sel.transform.scale[1] - dy * 0.015)
                elif self.active_gizmo_axis == 'z': sel.transform.scale[2] = max(0.1, sel.transform.scale[2] - dy * 0.015)
                elif self.active_gizmo_axis == 'center':
                    ns = max(0.1, sel.transform.scale[0] + (dx - dy) * 0.015)
                    sel.transform.scale = np.array([ns, ns, ns], np.float32)
            elif self.gizmo_mode == "rotate":
                if   self.active_gizmo_axis == 'x': sel.transform.rotation[0] = (sel.transform.rotation[0] + dy * 0.5) % 360
                elif self.active_gizmo_axis == 'y': sel.transform.rotation[1] = (sel.transform.rotation[1] + dx * 0.5) % 360
                elif self.active_gizmo_axis == 'z': sel.transform.rotation[2] = (sel.transform.rotation[2] + dx * 0.5) % 360
        else:
            if not pygame.mouse.get_pressed()[0]:
                self.is_dragging_gizmo = False
                self.active_gizmo_axis = None
            if self.is_dragging_object and 0 <= self.selected_index < len(self.editable_objects):
                sel = self.editable_objects[self.selected_index]
                mp  = pygame.mouse.get_pos()
                dx  = mp[0] - self.drag_object_last_mouse[0]
                dy  = mp[1] - self.drag_object_last_mouse[1]
                self.drag_object_last_mouse = mp
                yr = np.radians(self.camera_controller.yaw)
                pr = np.radians(self.camera_controller.pitch)
                right = np.array([np.cos(yr), 0.0, -np.sin(yr)], np.float32)
                up    = np.array([np.sin(pr) * np.sin(yr), np.cos(pr), np.sin(pr) * np.cos(yr)], np.float32)
                keys  = pygame.key.get_pressed()
                if keys[pygame.K_x]:
                    sel.transform.position -= up    * (dy * 0.015)
                    sel.transform.position  = self._snap(sel.transform.position)
                elif keys[pygame.K_z]:
                    sel.transform.position += right * (dx * 0.015)
                    sel.transform.position  = self._snap(sel.transform.position)
            elif not pygame.mouse.get_pressed()[0]:
                self.is_dragging_object = False

        for go in self.game_objects:
            go.update(dt)

    # -----------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        lay = self._lay

        if self.play_mode:
            # Configura câmera do editor para o lado esquerdo (Edit View)
            self.camera_comp.viewport_x = lay.viewport_edit_rect.x
            self.camera_comp.viewport_y = lay.viewport_edit_rect.y
            self.camera_comp.viewport_width = lay.viewport_edit_rect.width
            self.camera_comp.viewport_height = lay.viewport_edit_rect.height
            self.camera_comp.update(0.0)
            from engine.graphics.renderer3d import Camera3D
            Camera3D.main = self.camera_comp

            pygame.draw.rect(screen, T.VIEWPORT_BG, lay.viewport_edit_rect)
            self._draw_floor_grid(screen)
            for go in self.game_objects:
                go.draw(screen)
                if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                    r = go.get_component(MeshRenderer3D)
                    if r:
                        ow, oc, olw = r.wireframe, r.color, r.line_width
                        r.wireframe, r.color, r.line_width = True, T.ACCENT, 3
                        r.draw(screen)
                        r.wireframe, r.color, r.line_width = ow, oc, olw
            self._draw_gizmo(screen)
            self._draw_game_view(screen)
            pygame.draw.line(screen, T.BORDER,
                             (lay.viewport_split_x(), TOP_BAR_H),
                             (lay.viewport_split_x(), lay.screen_h), 2)
            self._draw_viewport_badge(screen, lay.viewport_edit_rect.x + 8,  TOP_BAR_H + 8,
                                      "EDIT MODE",       T.VIEWPORT_LABEL)
            self._draw_viewport_badge(screen, lay.viewport_game_rect.x + 8,  TOP_BAR_H + 8,
                                      "GAME VIEW (PLAY)", T.SUCCESS)
        else:
            # Configura câmera do editor para a tela cheia
            self.camera_comp.viewport_x = lay.viewport_rect.x
            self.camera_comp.viewport_y = lay.viewport_rect.y
            self.camera_comp.viewport_width = lay.viewport_rect.width
            self.camera_comp.viewport_height = lay.viewport_rect.height
            self.camera_comp.update(0.0)
            from engine.graphics.renderer3d import Camera3D
            Camera3D.main = self.camera_comp

            pygame.draw.rect(screen, T.VIEWPORT_BG, lay.viewport_rect)
            self._draw_floor_grid(screen)
            for go in self.game_objects:
                go.draw(screen)
                if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                    r = go.get_component(MeshRenderer3D)
                    if r:
                        ow, oc, olw = r.wireframe, r.color, r.line_width
                        r.wireframe, r.color, r.line_width = True, T.ACCENT, 3
                        r.draw(screen)
                        r.wireframe, r.color, r.line_width = ow, oc, olw
            self._draw_gizmo(screen)
            self._draw_viewport_badge(screen, lay.viewport_rect.x + 8, TOP_BAR_H + 8,
                                      "EDIT MODE", T.VIEWPORT_LABEL)

        self._draw_left_panel(screen)
        self._draw_top_bar(screen)
        self._draw_right_panel(screen)
        self._draw_xyz_widget(screen)
        self._draw_status_bar(screen)

        if self.showing_templates:
            self._draw_templates_modal(screen)
        elif self.code_editor.is_open:
            self.code_editor.draw(screen)
        elif self.showing_help_modal:
            self._draw_help_modal(screen)
        elif self.showing_welcome:
            self._draw_welcome_modal(screen)

    # -----------------------------------------------------------------------
    def _draw_viewport_badge(self, screen, x, y, text, color):
        from .gui import Badge
        bg = T.alpha_blend(color, 0.15, T.BG)
        Badge(x, y, text, color, bg).draw(screen, self.font_section)

    def _draw_game_view(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.VIEWPORT_BG, lay.viewport_game_rect)
        
        from engine.graphics.renderer3d import Camera3D
        # Procura câmera customizada na cena
        custom_cam = None
        for obj in self.editable_objects:
            if obj.active:
                cam_comp = obj.get_component(Camera3D)
                if cam_comp and cam_comp is not self.camera_comp:
                    custom_cam = cam_comp
                    break
        
        old_main = Camera3D.main
        
        try:
            if custom_cam:
                # Configura a câmera customizada do jogo para a viewport do jogo
                custom_cam.viewport_x = lay.viewport_game_rect.x
                custom_cam.viewport_y = lay.viewport_game_rect.y
                custom_cam.viewport_width = lay.viewport_game_rect.width
                custom_cam.viewport_height = lay.viewport_game_rect.height
                custom_cam.update(0.0)
                Camera3D.main = custom_cam
            else:
                # Fallback: move a câmera do editor temporariamente para a viewport do jogo
                self.camera_comp.viewport_x = lay.viewport_game_rect.x
                self.camera_comp.viewport_y = lay.viewport_game_rect.y
                self.camera_comp.viewport_width = lay.viewport_game_rect.width
                self.camera_comp.viewport_height = lay.viewport_game_rect.height
                self.camera_comp.update(0.0)
                Camera3D.main = self.camera_comp

            # Renderiza a game view
            for go in self.game_objects:
                go.draw(screen)
        finally:
            # Restaura a câmera do editor
            Camera3D.main = old_main
            self.camera_comp.viewport_x = lay.viewport_edit_rect.x if self.play_mode else lay.viewport_rect.x
            self.camera_comp.viewport_y = lay.viewport_edit_rect.y if self.play_mode else lay.viewport_rect.y
            self.camera_comp.viewport_width = lay.viewport_edit_rect.width if self.play_mode else lay.viewport_rect.width
            self.camera_comp.viewport_height = lay.viewport_edit_rect.height if self.play_mode else lay.viewport_rect.height
            self.camera_comp.update(0.0)

    def _draw_status_bar(self, screen: pygame.Surface) -> None:
        lay = self._lay
        bar_y = lay.screen_h - STATUS_BAR_H
        pygame.draw.rect(screen, T.PANEL, (0, bar_y, lay.screen_w, STATUS_BAR_H))
        pygame.draw.line(screen, T.BORDER, (0, bar_y), (lay.screen_w, bar_y))

        # Mensagem de status
        if self._status_timer > 0 and self._status_msg:
            kind = getattr(self, "_status_kind", "info")
            col  = T.SUCCESS if kind == "success" else (T.ERROR if kind == "error" else T.TEXT_MUTED)
            surf = self.font_section.render(f"  {self._status_msg}", True, col)
            screen.blit(surf, (4, bar_y + 4))
        else:
            # Informações padrão
            obj_count = len(self.editable_objects)
            sel_name  = self.editable_objects[self.selected_index].name if 0 <= self.selected_index < obj_count else "—"
            undo_info = f"Undo: {self.history.undo_count()}  Redo: {self.history.redo_count()}"
            mode_name = CAMERA_MODES[self.camera_mode_index]
            info = f"  Objetos: {obj_count}  |  Sel: {sel_name}  |  {undo_info}  |  Câmera: {mode_name}  |  Snap: {'ON' if self.snap_enabled else 'OFF'}"
            surf = self.font_section.render(info, True, T.TEXT_MUTED)
            screen.blit(surf, (4, bar_y + 4))

    def _draw_gizmo(self, screen: pygame.Surface) -> None:
        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            self.gizmo_screen_points = {}
            self.gizmo_screen_center = None
            return

        sel = self.editable_objects[self.selected_index]
        cam = self.camera_comp
        vx, vy, vw, vh = cam.viewport_x, cam.viewport_y, cam.viewport_width, cam.viewport_height

        pos = sel.transform.position
        axes = {
            'x': pos + np.array([0.8, 0.0, 0.0], np.float32),
            'y': pos + np.array([0.0, 0.8, 0.0], np.float32),
            'z': pos + np.array([0.0, 0.0, 0.8], np.float32),
        }

        def ts(i): return int(vx + (ndc[i, 0] + 1) * vw / 2), int(vy + (-ndc[i, 1] + 1) * vh / 2)

        verts = np.array([pos] + list(axes.values()), np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, cam.view_matrix, cam.projection_matrix)

        if depths[0] <= cam.near:
            return

        def draw_triangle(surface, color, pt, center):
            dx, dy = pt[0] - center[0], pt[1] - center[1]
            length = max(1, np.hypot(dx, dy))
            nx, ny = dx / length, dy / length
            p1 = (int(pt[0] + ny * 5), int(pt[1] - nx * 5))
            p2 = (int(pt[0] - ny * 5), int(pt[1] + nx * 5))
            pygame.draw.polygon(surface, color, [pt, p1, p2])

        center_s = ts(0)
        self.gizmo_screen_center = center_s

        colors_map  = {'x': T.GIZMO_X, 'y': T.GIZMO_Y, 'z': T.GIZMO_Z}
        new_pts: Dict[str, Tuple[int, int]] = {}

        for i, (axis, _) in enumerate(axes.items()):
            if depths[i + 1] > cam.near:
                pt = ts(i + 1)
                new_pts[axis] = pt
                col = colors_map[axis]
                pygame.draw.line(screen, col, center_s, pt, 2)
                draw_triangle(screen, col, pt, center_s)
                label = self.font_section.render(axis.upper(), True, col)
                screen.blit(label, (pt[0] + 4, pt[1] - 8))

        self.gizmo_screen_points = new_pts

        # Centro — círculo branco (uniform scale)
        if self.gizmo_mode == "scale":
            pygame.draw.circle(screen, (220, 220, 220), center_s, 5)
            pygame.draw.circle(screen, (50, 50, 50),    center_s, 5, 1)

    # -----------------------------------------------------------------------
    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL, (0, TOP_BAR_H, LEFT_PANEL_W, lay.screen_h))
        pygame.draw.line(screen, T.BORDER, (LEFT_PANEL_W, TOP_BAR_H), (LEFT_PANEL_W, lay.screen_h))

        # Seção: Adicionar Objetos
        SectionHeader(LEFT_PADDING, ADD_SECTION_Y, LEFT_PANEL_W - LEFT_PADDING * 2, "Adicionar Objeto").draw(screen, self.font_section)
        for btn in [self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
                    self.btn_add_plane, self.btn_add_capsule, self.btn_add_camera, self.btn_add_light]:
            btn.draw(screen, self.font_btn)

        # Seção: Gizmo
        SectionHeader(LEFT_PADDING, GIZMO_SECTION_Y, LEFT_PANEL_W - LEFT_PADDING * 2, "Gizmo").draw(screen, self.font_section)
        for btn in [self.btn_mode_translate, self.btn_mode_rotate, self.btn_mode_scale]:
            col = T.ACCENT if (
                (btn is self.btn_mode_translate and self.gizmo_mode == "translate") or
                (btn is self.btn_mode_rotate    and self.gizmo_mode == "rotate")    or
                (btn is self.btn_mode_scale     and self.gizmo_mode == "scale")
            ) else btn.bg_color
            orig = btn.bg_color
            btn.bg_color = col
            btn.draw(screen, self.font_btn)
            btn.bg_color = orig

        # Snap + Templates
        self.btn_snap.draw(screen, self.font_btn)
        self.btn_templates.draw(screen, self.font_btn)

        # Árvore de objetos
        tree = self._build_flat_tree()
        tree_clip = pygame.Rect(0, TREE_Y, LEFT_PANEL_W, lay.tree_h)
        screen.set_clip(tree_clip)

        for i, (obj, depth) in enumerate(tree):
            vis_i = i - self._tree_scroll
            if vis_i < 0:
                continue
            if vis_i * TREE_ROW_H >= lay.tree_h:
                break

            row_y = TREE_Y + vis_i * TREE_ROW_H
            row   = pygame.Rect(0, row_y, LEFT_PANEL_W, TREE_ROW_H)

            actual_i = self.editable_objects.index(obj) if obj in self.editable_objects else -1
            selected = (actual_i == self.selected_index)

            bg = T.ACCENT_BG if selected else (T.SURFACE if vis_i % 2 == 0 else T.SURFACE_2)
            pygame.draw.rect(screen, bg, row)

            icon = _SHAPE_ICON.get(obj.name.rstrip("0123456789").replace("_clone", ""), "▣")
            indent = LEFT_PADDING + depth * 12

            if self._rename_index == actual_i:
                # Campo de rename
                self._rename_blink += 0.016
                cursor = "|" if int(self._rename_blink * 2) % 2 == 0 else ""
                text   = self._rename_text + cursor
                surf   = self.font_body.render(text, True, T.ACCENT)
            else:
                col  = T.TEXT_PRIMARY if selected else T.TEXT_MUTED
                surf = self.font_body.render(f"{icon} {obj.name}", True, col)

            screen.blit(surf, (indent, row_y + 2))

        screen.set_clip(None)

        # Scroll arrows
        self.btn_tree_up.draw(screen, self.font_btn)
        self.btn_tree_down.draw(screen, self.font_btn)

        # Undo / Redo / Delete
        self.btn_undo.draw(screen, self.font_btn)
        self.btn_redo.draw(screen, self.font_btn)
        self.btn_delete.draw(screen, self.font_btn)

        # Ângulo de luz
        lay_ls = lay.light_section_y
        SectionHeader(LEFT_PADDING, lay_ls - 16, LEFT_PANEL_W - LEFT_PADDING * 2, "Luz").draw(screen, self.font_section)
        self.btn_light_angle_dec.draw(screen, self.font_btn)
        self.btn_light_angle_inc.draw(screen, self.font_btn)
        angle_surf = self.font_body.render(f"{int(self.light_angle)}°", True, T.TEXT_PRIMARY)
        screen.blit(angle_surf, (LEFT_PADDING + 44, lay_ls + 2))

    # -----------------------------------------------------------------------
    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL, (0, 0, lay.screen_w, TOP_BAR_H))
        pygame.draw.line(screen, T.BORDER, (0, TOP_BAR_H - 1), (lay.screen_w, TOP_BAR_H - 1))

        # Logo "Zennity"
        logo_surf = self.font_xyz.render("ZENNITY", True, T.ACCENT)
        screen.blit(logo_surf, (12, 4))

        # Menus
        for btn in [self.btn_menu_file, self.btn_menu_view, self.btn_menu_window]:
            btn.draw(screen, self.font_btn)

        # PLAY
        self.btn_play_pause.draw(screen, self.font_btn)

        # Modo da câmera (Badge)
        mode_name = CAMERA_MODES[self.camera_mode_index]
        from .gui import Badge
        Badge(lay.play_button_x + 96, 4, f"Câmera: {mode_name}", T.TEXT_PRIMARY, T.SURFACE_2).draw(screen, self.font_section)

        # Dropdowns
        if self._active_dropdown:
            self._draw_dropdowns(screen)

    def _draw_dropdowns(self, screen: pygame.Surface) -> None:
        if self._active_dropdown == "file":
            items = [("Novo",     None), ("Salvar", None), ("Carregar", None)]
            rx_d, ry_d = 110, TOP_BAR_H
            dw, dh = 120, len(items) * 26 + 4
            pygame.draw.rect(screen, T.SURFACE, (rx_d, ry_d, dw, dh), border_radius=4)
            pygame.draw.rect(screen, T.BORDER,  (rx_d, ry_d, dw, dh), 1, border_radius=4)
            mx, my = pygame.mouse.get_pos()
            for i, (label, _) in enumerate(items):
                r = pygame.Rect(rx_d + 2, ry_d + 2 + i * 26, dw - 4, 24)
                bg = T.SURFACE_2 if r.collidepoint(mx, my) else T.SURFACE
                pygame.draw.rect(screen, bg, r, border_radius=3)
                surf = self.font_body.render(label, True, T.TEXT_PRIMARY)
                screen.blit(surf, (r.x + 8, r.y + 4))

    # -----------------------------------------------------------------------
    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        lay = self._lay
        rx  = lay.inspector_x()
        panel_x = lay.screen_w - RIGHT_PANEL_W

        pygame.draw.rect(screen, T.PANEL, (panel_x, TOP_BAR_H, RIGHT_PANEL_W, lay.screen_h))
        pygame.draw.line(screen, T.BORDER, (panel_x, TOP_BAR_H), (panel_x, lay.screen_h))

        if self.selected_index < 0 or self.selected_index >= len(self.editable_objects):
            msg = self.font_body.render("Nenhum objeto selecionado", True, T.TEXT_MUTED)
            screen.blit(msg, (rx, INSP_HEADER_Y))
            return

        sel = self.editable_objects[self.selected_index]
        pos = sel.transform.position
        rot = sel.transform.rotation
        sc  = sel.transform.scale

        # Nome (fixo no topo)
        name_surf = self.font_xyz.render(sel.name, True, T.TEXT_PRIMARY)
        screen.blit(name_surf, (rx, INSP_HEADER_Y))

        # Configura clipping da área rolável
        inspect_clip = pygame.Rect(panel_x, TOP_BAR_H + 45, RIGHT_PANEL_W, lay.screen_h - TOP_BAR_H - STATUS_BAR_H - 50)
        screen.set_clip(inspect_clip)

        scroll = getattr(self, "_inspector_scroll", 0)
        phys_y = INSP_PHYSICS_Y - scroll
        script_y = INSP_SCRIPT_Y - scroll
        color_y = INSP_COLOR_Y - scroll
        clone_y = INSP_CLONE_Y - scroll
        hier_y = INSP_HIER_Y - scroll
        tag_y = INSP_TAG_Y - scroll
        trans_y = INSP_TRANSFORM_Y - scroll

        Divider(rx, phys_y - 20, INSPECTOR_W).draw(screen)

        # Física
        SectionHeader(rx, phys_y - 12, INSPECTOR_W, "Física").draw(screen, self.font_section)

        is_static = getattr(sel, "is_static", False)
        self.btn_toggle_static.label = "☑" if is_static else "☐"
        self.btn_toggle_static.draw(screen, self.font_btn)
        screen.blit(self.font_body.render("Estático", True, T.TEXT_PRIMARY), (rx + 24, phys_y - 10))

        phys_on = getattr(sel, "physics_enabled", False)
        self.btn_toggle_physics.label = "☑" if phys_on else "☐"
        self.btn_toggle_physics.draw(screen, self.font_btn)
        screen.blit(self.font_body.render("Física ativa", True, T.TEXT_PRIMARY), (rx + 24, phys_y + 20))

        # Velocidade
        vel = getattr(sel, "_velocity", np.zeros(3))
        vel_surf = self.font_section.render(f"vel: {vel[0]:+.1f}, {vel[1]:+.1f}, {vel[2]:+.1f}", True, T.TEXT_MUTED)
        screen.blit(vel_surf, (rx, phys_y + 50))
        self.btn_vel_dec.draw(screen, self.font_btn)
        self.btn_vel_inc.draw(screen, self.font_btn)

        Divider(rx, script_y - 8, INSPECTOR_W).draw(screen)

        # Script
        SectionHeader(rx, script_y, INSPECTOR_W, "Script").draw(screen, self.font_section)
        cur_script = getattr(sel, "_script_name", "Nenhum")
        from .gui import Badge
        Badge(rx + 32, script_y + 2, cur_script, T.ACCENT, T.ACCENT_BG).draw(screen, self.font_body)
        for btn in [self.btn_prev_script, self.btn_next_script,
                    self.btn_new_script, self.btn_edit_script,
                    self.btn_internal_editor, self.btn_script_help]:
            btn.draw(screen, self.font_btn)

        Divider(rx, color_y - 4, INSPECTOR_W).draw(screen)

        # Cor
        SectionHeader(rx, color_y + 4, INSPECTOR_W, "Cor").draw(screen, self.font_section)
        r_comp = sel.get_component(MeshRenderer3D)
        for i, btn in enumerate(self.btn_colors):
            btn.draw(screen, self.font_btn)
            if r_comp and tuple(r_comp.color) == COLOR_PALETTE[i]:
                # Indicador de cor ativa (borda branca com respiro)
                border_rect = pygame.Rect(btn.rect.x - 2, btn.rect.y - 2, btn.rect.w + 4, btn.rect.h + 4)
                pygame.draw.rect(screen, (255, 255, 255), border_rect, 2, border_radius=5)
                
        if r_comp:
            cur_col = r_comp.color
            pygame.draw.rect(screen, cur_col,   (rx, color_y + 56, INSPECTOR_W, 12), border_radius=3)
            pygame.draw.rect(screen, T.BORDER,  (rx, color_y + 56, INSPECTOR_W, 12), 1, border_radius=3)

        Divider(rx, clone_y - 8, INSPECTOR_W).draw(screen)

        self.btn_clone.draw(screen, self.font_btn)

        Divider(rx, hier_y - 4, INSPECTOR_W).draw(screen)

        # Pai
        SectionHeader(rx, hier_y, INSPECTOR_W, "Pai (Hierarquia)").draw(screen, self.font_section)
        self.btn_prev_parent.draw(screen, self.font_btn)
        self.btn_next_parent.draw(screen, self.font_btn)
        parent_name = sel.parent.name if getattr(sel, "parent", None) else "(raiz)"
        Badge(rx + 32, hier_y + 3, parent_name, T.TEXT_PRIMARY, T.SURFACE_2).draw(screen, self.font_body)

        Divider(rx, tag_y - 4, INSPECTOR_W).draw(screen)

        # Tag
        SectionHeader(rx, tag_y, INSPECTOR_W, "Tag").draw(screen, self.font_section)
        self.btn_prev_tag.draw(screen, self.font_btn)
        self.btn_next_tag.draw(screen, self.font_btn)
        tag_name = getattr(sel, "tag", "") or "(sem tag)"
        Badge(rx + 32, tag_y + 3, tag_name, T.ACCENT, T.ACCENT_BG).draw(screen, self.font_body)

        Divider(rx, trans_y - 4, INSPECTOR_W).draw(screen)

        # Transform
        SectionHeader(rx, trans_y, INSPECTOR_W, "Transform").draw(screen, self.font_section)
        labels = [("X", T.GIZMO_X), ("Y", T.GIZMO_Y), ("Z", T.GIZMO_Z)]
        for row_i, (label, col_c) in enumerate(labels):
            y_base = trans_y + 16 + row_i * 68
            # POS
            screen.blit(self.font_section.render(f"POS {label}", True, col_c), (rx, y_base))
            screen.blit(self.font_xyz.render(f"{pos[row_i]:+.2f}", True, T.TEXT_PRIMARY), (rx + 55, y_base))
            # ROT
            screen.blit(self.font_section.render(f"ROT {label}", True, col_c), (rx, y_base + 20))
            screen.blit(self.font_xyz.render(f"{rot[row_i]:+.1f}°", True, T.TEXT_PRIMARY), (rx + 55, y_base + 20))
            # SCL
            screen.blit(self.font_section.render(f"SCL {label}", True, col_c), (rx, y_base + 40))
            screen.blit(self.font_xyz.render(f"{sc[row_i]:+.2f}",  True, T.TEXT_PRIMARY), (rx + 55, y_base + 40))

        screen.set_clip(None)

    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        """Mini widget XYZ no canto superior direito da viewport."""
        lay = self._lay
        wx = lay.viewport_rect.right - 60
        wy = TOP_BAR_H + 8
        labels = [("X", T.GIZMO_X), ("Y", T.GIZMO_Y), ("Z", T.GIZMO_Z)]
        for i, (label, col) in enumerate(labels):
            screen.blit(self.font_section.render(label, True, col), (wx + i * 20, wy))

    # -----------------------------------------------------------------------
    # Modais
    # -----------------------------------------------------------------------

    def _modal_overlay(self, screen: pygame.Surface, w: int, h: int) -> pygame.Rect:
        """Desenha o overlay escuro e retorna o rect do modal centralizado."""
        sw, sh = self._lay.screen_w, self._lay.screen_h
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        mx = (sw - w) // 2
        my = (sh - h) // 2
        rect = pygame.Rect(mx, my, w, h)
        pygame.draw.rect(screen, T.PANEL,   rect, border_radius=8)
        pygame.draw.rect(screen, T.BORDER,  rect, 1, border_radius=8)
        return rect

    def _draw_welcome_modal(self, screen: pygame.Surface) -> None:
        """Modal de boas-vindas passo-a-passo para novos usuários."""
        total_steps = len(WELCOME_STEPS)
        step = max(0, min(self.welcome_step, total_steps - 1))
        title, body = WELCOME_STEPS[step]

        mw, mh = 500, 200
        rect = self._modal_overlay(screen, mw, mh)
        mx, my = rect.x, rect.y

        # Barra de progresso
        prog_w = int((mw - 20) * (step + 1) / total_steps)
        pygame.draw.rect(screen, T.SURFACE_2,  (mx + 10, my + 8,    mw - 20, 4), border_radius=2)
        pygame.draw.rect(screen, T.ACCENT,     (mx + 10, my + 8,    prog_w,  4), border_radius=2)

        # Contador
        counter = self.font_section.render(f"{step + 1} / {total_steps}", True, T.TEXT_MUTED)
        screen.blit(counter, (mx + mw - counter.get_width() - 12, my + 16))

        # Título
        title_surf = self.font_xyz.render(title, True, T.TEXT_PRIMARY)
        screen.blit(title_surf, (mx + 20, my + 22))

        # Separador
        pygame.draw.line(screen, T.BORDER, (mx + 20, my + 46), (mx + mw - 20, my + 46), 1)

        # Corpo — quebra de linha automática
        words = body.split(" ")
        lines, line = [], ""
        for word in words:
            test = (line + " " + word).strip()
            if self.font_body.size(test)[0] > mw - 40:
                if line:
                    lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)

        for i, ln in enumerate(lines):
            screen.blit(self.font_body.render(ln, True, T.TEXT_PRIMARY), (mx + 20, my + 54 + i * 20))

        # Botões (posicionados pelo _reposition_buttons)
        btn_y = my + mh - 46
        if step > 0:
            self.btn_welcome_prev.y = btn_y
            self.btn_welcome_prev.draw(screen, self.font_btn)
        self.btn_welcome_close.y = btn_y
        self.btn_welcome_close.draw(screen, self.font_btn)
        if step < total_steps - 1:
            self.btn_welcome_next.y = btn_y
            self.btn_welcome_next.draw(screen, self.font_btn)

    def _draw_help_modal(self, screen: pygame.Surface) -> None:
        """Modal de ajuda com todos os atalhos e comandos."""
        mw, mh = 560, min(520, self._lay.screen_h - 60)
        rect = self._modal_overlay(screen, mw, mh)
        mx, my = rect.x, rect.y

        # Cabeçalho
        title_surf = self.font_xyz.render("Guia de Comandos", True, T.ACCENT)
        screen.blit(title_surf, (mx + 20, my + 14))
        pygame.draw.line(screen, T.BORDER, (mx + 20, my + 36), (mx + mw - 20, my + 36), 1)

        # Linhas de conteúdo com scroll implícito (clip)
        clip_rect = pygame.Rect(mx + 10, my + 40, mw - 20, mh - 80)
        screen.set_clip(clip_rect)
        for i, ln in enumerate(HELP_LINES):
            y = my + 44 + i * 17
            if y > my + mh - 50:
                break
            col = T.ACCENT if ln and not ln.startswith(" ") else T.TEXT_PRIMARY
            screen.blit(self.font_section.render(ln, True, col), (mx + 16, y))
        screen.set_clip(None)

        # Botão fechar
        close_w, close_h = 100, 26
        close_x = mx + (mw - close_w) // 2
        close_y = my + mh - close_h - 10
        close_rect = pygame.Rect(close_x, close_y, close_w, close_h)
        mpos = pygame.mouse.get_pos()
        bg = T.BTN_DANGER_HOVER if close_rect.collidepoint(mpos) else T.BTN_DANGER
        pygame.draw.rect(screen, bg, close_rect, border_radius=4)
        lbl = self.font_btn.render("Fechar  [Esc]", True, T.TEXT_PRIMARY)
        screen.blit(lbl, (close_x + (close_w - lbl.get_width()) // 2,
                          close_y + (close_h - lbl.get_height()) // 2))

    def _draw_templates_modal(self, screen: pygame.Surface) -> None:
        """Modal de seleção de templates de cena."""
        num = max(len(self._template_list), 1)
        mw  = 500
        mh  = min(120 + num * 60 + 50, self._lay.screen_h - 60)
        rect = self._modal_overlay(screen, mw, mh)
        mx, my = rect.x, rect.y

        # Cabeçalho
        title_surf = self.font_xyz.render("Carregar Template", True, T.ACCENT)
        screen.blit(title_surf, (mx + 20, my + 14))
        pygame.draw.line(screen, T.BORDER, (mx + 20, my + 36), (mx + mw - 20, my + 36), 1)

        if not self._template_list:
            msg = self.font_body.render(
                "Nenhum template encontrado em demos/template_*.json",
                True, T.TEXT_MUTED,
            )
            screen.blit(msg, (mx + 20, my + 50))
        else:
            # Reposiciona e desenha botões de template
            for i, (btn, tpl) in enumerate(zip(self.btn_template_items, self._template_list)):
                btn.x = mx + 20
                btn.y = my + 46 + i * 60
                btn.w = mw - 40
                btn.draw(screen, self.font_btn)
                # Subtítulo do template
                desc = tpl.get("_template_desc", "")
                if desc:
                    ds = self.font_section.render(desc, True, T.TEXT_MUTED)
                    screen.blit(ds, (btn.x + 10, btn.y + btn.h - 18))

        # Botão fechar (reposicionado pelo _reposition_buttons)
        self.btn_templates_close.draw(screen, self.font_btn)

    # -----------------------------------------------------------------------
    # Processamento de Eventos (CORRIGIDO — método estava ausente)
    # -----------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:  # noqa: C901
        lay = self._lay

        # ── Scroll do mouse — zoom da câmera / scroll de painéis ──────────────
        if event.type == pygame.MOUSEWHEEL:
            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
            else:
                mx, my = pygame.mouse.get_pos()
                panel_x = lay.screen_w - RIGHT_PANEL_W
                if mx >= panel_x:
                    self._inspector_scroll = max(0, min(500, self._inspector_scroll - event.y * 30))
                    self._reposition_buttons()
                else:
                    self.camera_controller.target_distance = max(
                        1.0, self.camera_controller.target_distance - event.y * 0.5
                    )
            return

        # ── Teclado ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN:
            # Undo / Redo
            if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                if event.mod & pygame.KMOD_SHIFT:
                    self.history.redo(self)
                    self._notify("Refazer", "info")
                else:
                    self.history.undo(self)
                    self._notify("Desfazer", "info")
                return

            # Escape — fecha modais na ordem de prioridade
            if event.key == pygame.K_ESCAPE:
                if self.code_editor.is_open:
                    self.code_editor.close()
                elif self.showing_help_modal:
                    self.showing_help_modal = False
                elif self.showing_templates:
                    self.showing_templates = False
                elif self.showing_welcome:
                    self.showing_welcome = False
                return

            # Rename em andamento — captura teclado
            if self._rename_index >= 0:
                if event.key == pygame.K_RETURN:
                    self._commit_rename()
                elif event.key == pygame.K_BACKSPACE:
                    self._rename_text = self._rename_text[:-1]
                elif event.unicode and event.unicode.isprintable():
                    self._rename_text += event.unicode
                return

            # Code editor aberto — redireciona teclado
            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
                return

            # Delete selecionado
            if event.key == pygame.K_DELETE and self.selected_index >= 0:
                self.delete_selected()

        # ── Clique esquerdo ──────────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Modais têm prioridade máxima
            if self.showing_welcome:
                if self.btn_welcome_close.is_clicked(event):
                    self.showing_welcome = False
                elif self.btn_welcome_next.is_clicked(event):
                    if self.welcome_step < len(WELCOME_STEPS) - 1:
                        self.welcome_step += 1
                elif self.btn_welcome_prev.is_clicked(event):
                    if self.welcome_step > 0:
                        self.welcome_step -= 1
                return

            if self.showing_help_modal:
                self.showing_help_modal = False
                return

            if self.showing_templates:
                if self.btn_templates_close.is_clicked(event):
                    self.showing_templates = False
                else:
                    for btn, tpl in zip(self.btn_template_items, self._template_list):
                        if btn.is_clicked(event):
                            self._load_template(tpl)
                            self.showing_templates = False
                            self._notify(f"Template '{tpl.get('_template_name','?')}' carregado", "success")
                            break
                return

            if self.code_editor.is_open:
                self.code_editor.handle_event(event)
                return

            # ── Barra superior ───────────────────────────────────────────────
            if self.btn_play_pause.is_clicked(event):
                if not self.play_mode:
                    self.play_mode = True
                    self.saved_scene_state = []
                    for obj in self.editable_objects:
                        self.saved_scene_state.append({
                            "obj": obj,
                            "pos": obj.transform.position.copy(),
                            "rot": obj.transform.rotation.copy(),
                            "sc":  obj.transform.scale.copy(),
                        })
                        PhysicsSim.attach_rigidbody(obj)
                        ScriptManager.load(obj)
                    self.btn_play_pause.label = "⏹  STOP"
                    self._notify("Play iniciado", "success")
                else:
                    self.play_mode = False
                    if self.saved_scene_state:
                        for state in self.saved_scene_state:
                            o = state["obj"]
                            o.transform.position = state["pos"]
                            o.transform.rotation = state["rot"]
                            o.transform.scale    = state["sc"]
                            PhysicsSim.detach_rigidbody(o)
                            ScriptManager.unload(o)
                    self.saved_scene_state = None
                    PhysicsSim.clear_registries()
                    self.btn_play_pause.label = "▶  PLAY"
                    self._notify("Play encerrado", "info")
                return

            if self.btn_menu_file.is_clicked(event):
                self._active_dropdown = "file" if self._active_dropdown != "file" else None
                return
            if self.btn_menu_view.is_clicked(event):
                self._active_dropdown = "view" if self._active_dropdown != "view" else None
                return
            if self.btn_menu_window.is_clicked(event):
                self._active_dropdown = "window" if self._active_dropdown != "window" else None
                return

            # Fecha dropdown ao clicar fora / processa clique nos itens
            if self._active_dropdown:
                if self._active_dropdown == "file":
                    rx_d, ry_d = 110, TOP_BAR_H
                    for i, (label, action) in enumerate([
                        ("Novo",     self._new_scene),
                        ("Salvar",   self.save_scene),
                        ("Carregar", self.load_scene),
                    ]):
                        r = pygame.Rect(rx_d + 2, ry_d + 2 + i * 26, 116, 24)
                        if r.collidepoint(mx, my):
                            action()
                            self._active_dropdown = None
                            return
                self._active_dropdown = None

            # ── Painel esquerdo — formas ─────────────────────────────────────
            if self.btn_add_cube.is_clicked(event):    self.spawn_object("Cube");    return
            if self.btn_add_pyramid.is_clicked(event): self.spawn_object("Pyramid"); return
            if self.btn_add_sphere.is_clicked(event):  self.spawn_object("Sphere");  return
            if self.btn_add_plane.is_clicked(event):   self.spawn_object("Plane");   return
            if self.btn_add_capsule.is_clicked(event): self.spawn_object("Capsule"); return
            if self.btn_add_camera.is_clicked(event):  self.spawn_object("Camera");  return
            if self.btn_add_light.is_clicked(event):   self.spawn_object("Light");   return

            # ── Gizmo modes ──────────────────────────────────────────────────
            if self.btn_mode_translate.is_clicked(event): self.gizmo_mode = "translate"; return
            if self.btn_mode_rotate.is_clicked(event):    self.gizmo_mode = "rotate";    return
            if self.btn_mode_scale.is_clicked(event):     self.gizmo_mode = "scale";     return

            # ── Snap + Templates ─────────────────────────────────────────────
            if self.btn_snap.is_clicked(event):
                self.snap_enabled = not self.snap_enabled
                self.btn_snap.label = f"Grade: {'ON' if self.snap_enabled else 'OFF'}"
                return
            if self.btn_templates.is_clicked(event):
                self.showing_templates = True
                return

            # ── Undo / Redo / Delete / Luz ───────────────────────────────────
            # ── Undo / Redo / Delete / Luz ───────────────────────────────────
            if self.btn_undo.is_clicked(event):
                self.history.undo(self); self._notify("Desfazer", "info"); return
            if self.btn_redo.is_clicked(event):
                self.history.redo(self); self._notify("Refazer",  "info"); return

            # Scrollbar do Outliner
            if self.btn_tree_up.is_clicked(event):
                self._tree_scroll = max(0, self._tree_scroll - 1)
                return
            if self.btn_tree_down.is_clicked(event):
                self._tree_scroll = min(self._max_scroll(), self._tree_scroll + 1)
                return

            if self.btn_light_angle_dec.is_clicked(event) or self.btn_light_angle_inc.is_clicked(event):
                delta = -15.0 if self.btn_light_angle_dec.is_clicked(event) else 15.0
                self.light_angle = (self.light_angle + delta) % 360
                rad = np.radians(self.light_angle)
                ld = np.array([np.cos(rad), 1.0, np.sin(rad)], np.float32)
                ld /= np.linalg.norm(ld)
                for obj in self.editable_objects:
                    r = obj.get_component(MeshRenderer3D)
                    if r:
                        r.light_dir = ld
                return

            # Clique para selecionar objeto na viewport ou na árvore
            if self.click_start_pos:
                dx = event.pos[0] - self.click_start_pos[0]
                dy = event.pos[1] - self.click_start_pos[1]
                if np.hypot(dx, dy) < 4.0:
                    # Seleção de objeto na árvore
                    if mx < LEFT_PANEL_W:
                        tree_rect = pygame.Rect(0, TREE_Y, LEFT_PANEL_W, lay.tree_h)
                        if tree_rect.collidepoint(mx, my):
                            slot_i = (my - TREE_Y) // TREE_ROW_H
                            obj_i = self._tree_scroll + slot_i
                            flat_tree = self._build_flat_tree()
                            if 0 <= obj_i < len(flat_tree):
                                clicked_obj, depth = flat_tree[obj_i]
                                real_idx = self.editable_objects.index(clicked_obj)
                                now = pygame.time.get_ticks() / 1000.0
                                if real_idx == self._last_click_index and (now - self._last_click_time) < 0.4:
                                    self._start_rename(real_idx)
                                else:
                                    self.selected_index = real_idx
                                self._last_click_index = real_idx
                                self._last_click_time = now
                    # Seleção de objeto na viewport 3D (apenas no lado do Edit View se split)
                    elif mx <= (lay.viewport_edit_rect.right if self.play_mode else lay.viewport_rect.right):
                        self._select_at(mx, my)
                self.click_start_pos = None
                return

        # ── Mouse button up ──────────────────────────────────────────────────
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging_gizmo or self.is_dragging_object:
                self.history.push(self)
            self.is_dragging_object = False
            self.is_dragging_gizmo = False
            self.active_gizmo_axis = None
            
            if self._is_dragging_tree:
                self._is_dragging_tree = False
                mx, my = event.pos
                tree_rect = pygame.Rect(0, TREE_Y, LEFT_PANEL_W, lay.tree_h)
                if tree_rect.collidepoint(mx, my):
                    slot_i = (my - TREE_Y) // TREE_ROW_H
                    obj_i = self._tree_scroll + slot_i
                    flat_tree = self._build_flat_tree()
                    if 0 <= obj_i < len(flat_tree):
                        target_parent = flat_tree[obj_i][0]
                        if target_parent != self._drag_tree_src:
                            # Evita dependência cíclica
                            curr = target_parent
                            loop = False
                            while curr:
                                if curr == self._drag_tree_src:
                                    loop = True
                                    break
                                curr = curr.parent
                            if not loop:
                                self.history.push(self)
                                self._drag_tree_src.parent = target_parent
                    else:
                        self.history.push(self)
                        self._drag_tree_src.parent = None
                else:
                    self.history.push(self)
                    self._drag_tree_src.parent = None

                if self.click_start_pos:
                    dx = event.pos[0] - self.click_start_pos[0]
                    dy = event.pos[1] - self.click_start_pos[1]
                    if np.hypot(dx, dy) < 4.0:
                        real_idx = self.editable_objects.index(self._drag_tree_src)
                        now = pygame.time.get_ticks() / 1000.0
                        if real_idx == self._last_click_index and (now - self._last_click_time) < 0.4:
                            self._start_rename(real_idx)
                        else:
                            self.selected_index = real_idx
                        self._last_click_index = real_idx
                        self._last_click_time = now
                self.click_start_pos = None
                return

        # ── Eventos do Inspector (só funcionam se houver objeto selecionado) ────
        if 0 <= self.selected_index < len(self.editable_objects):
            sel = self.editable_objects[self.selected_index]
            
            if self.btn_delete.is_clicked(event):
                self.delete_selected()
                return
            if self.btn_toggle_static.is_clicked(event):
                self.history.push(self)
                sel.is_static = not getattr(sel, "is_static", False)
                return
            if self.btn_toggle_physics.is_clicked(event):
                self.history.push(self)
                sel.physics_enabled = not getattr(sel, "physics_enabled", False)
                return
            if self.btn_vel_dec.is_clicked(event):
                self.history.push(self)
                sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) - 1.0
                if hasattr(sel, "_velocity"):
                    sel._velocity[1] = sel.initial_velocity_y
                return
            if self.btn_vel_inc.is_clicked(event):
                self.history.push(self)
                sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) + 1.0
                if hasattr(sel, "_velocity"):
                    sel._velocity[1] = sel.initial_velocity_y
                return
            if self.btn_clone.is_clicked(event):
                self.clone_selected()
                return
            if self.btn_prev_script.is_clicked(event) or self.btn_next_script.is_clicked(event):
                cur = getattr(sel, "script_path", "")
                idx = self.available_scripts.index(cur) if cur in self.available_scripts else 0
                delta = -1 if self.btn_prev_script.is_clicked(event) else 1
                ni = (idx + delta) % len(self.available_scripts)
                sel.script_path = self.available_scripts[ni] if ni > 0 else ""
                return
            if self.btn_new_script.is_clicked(event):
                path = ScriptManager.create_template(sel)
                self.available_scripts = ScriptManager.list_scripts()
                sel.script_path = path
                return
            if self.btn_edit_script.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p):
                    try:
                        os.startfile(p)
                    except:
                        import subprocess
                        subprocess.Popen(["notepad.exe", p])
                return
            if self.btn_internal_editor.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p):
                    self.code_editor.open(p)
                return
            if self.btn_script_help.is_clicked(event):
                self.showing_help_modal = True
                return
            
            # Parenting cycling
            if self.btn_prev_parent.is_clicked(event) or self.btn_next_parent.is_clicked(event):
                def is_descendant(p, child):
                    if p == child:
                        return True
                    if p.parent is None:
                        return False
                    return is_descendant(p.parent, child)
                candidates = [None] + [o for o in self.editable_objects if o != sel and not is_descendant(o, sel)]
                cur_parent = sel.parent
                try:
                    pi = candidates.index(cur_parent)
                except:
                    pi = 0
                delta = -1 if self.btn_prev_parent.is_clicked(event) else 1
                pi = (pi + delta) % len(candidates)
                new_parent = candidates[pi]
                self.history.push(self)
                if cur_parent:
                    cur_parent.remove_child(sel)
                if new_parent:
                    new_parent.add_child(sel)
                return
                
            # Tag cycling
            if self.btn_prev_tag.is_clicked(event) or self.btn_next_tag.is_clicked(event):
                cur_tag = getattr(sel, "tag", "")
                try:
                    ti = TAG_OPTIONS.index(cur_tag)
                except:
                    ti = 0
                delta = -1 if self.btn_prev_tag.is_clicked(event) else 1
                ti = (ti + delta) % len(TAG_OPTIONS)
                sel.tag = TAG_OPTIONS[ti]
                return
            for i, btn in enumerate(self.btn_colors):
                if btn.is_clicked(event):
                    self.history.push(self)
                    r = sel.get_component(MeshRenderer3D)
                    if r:
                        r.color = COLOR_PALETTE[i]
                    return