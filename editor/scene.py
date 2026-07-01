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
    (200, 200, 200), (220,  50,  50), ( 50, 170,  50),
    ( 50, 100, 220), (240, 200,   0), (200,  50, 200),
]

TAG_OPTIONS = ["", "player", "inimigo", "perigoso", "coletavel", "chao"]

HELP_LINES = [
    "Atalhos de teclado:",
    "  Ctrl+Z           Desfazer (Undo)",
    "  Ctrl+Shift+Z     Refazer (Redo)",
    "  Ctrl+D           Clonar objeto selecionado",
    "  Delete           Excluir objeto selecionado",
    "  G                Ativar/desativar snap de grade (0.5)",
    "  Scroll Mouse     Zoom da câmera",
    "  Botão Direito    Orbitar câmera",
    "",
    "Scripts prontos (selecione no inspetor):",
    "  builtin_wasd.py          Mover com WASD",
    "  builtin_jump.py          Pular com Espaço",
    "  builtin_rotate.py        Rotação contínua",
    "  builtin_follow_player.py Seguir o jogador",
    "  builtin_destroy_on_collision.py  Desaparecer ao colidir",
    "",
    "Tags (para scripts de colisão):",
    "  Defina a tag do objeto no inspetor direito.",
    "  Use getattr(outro_obj, 'tag', '') para checar.",
    "",
    "Áudio em scripts:",
    "  from engine.audio import AudioManager",
    "  AudioManager.play('sons/pulo.wav')",
    "  AudioManager.stop_all()",
    "",
    "Pulo com RigidBody3D:",
    "  from engine.physics.rigidbody3d import RigidBody3D",
    "  rb = obj.get_component(RigidBody3D)",
    "  if rb and Input.get_key_down(pygame.K_SPACE): rb.add_impulse(0, 5, 0)",
]

WELCOME_STEPS = [
    ("Bem-vindo à Zennity Engine! 🎮",
     "Esta é a tela do editor 3D. Aqui você cria seus jogos sem escrever código."),
    ("Adicionar Objetos",
     "Clique em '+ Cubo', '+ Pirâm' ou '+ Esf' no painel esquerdo para adicionar objetos à cena."),
    ("Templates prontos",
     "Clique em 'Templates' para carregar uma cena pronta: Plataformer, Arremesso ou Sandbox."),
    ("Propriedades do objeto",
     "Clique num objeto para selecioná-lo. No painel direito você ajusta posição, tamanho, cor, física e scripts."),
    ("Scripts prontos",
     "No inspetor, use '< >' para escolher um script pronto. Ex: builtin_wasd.py move o objeto com WASD."),
    ("Tags para colisões",
     "Defina a 'Tag' do objeto (ex: player, inimigo). Scripts podem detectar colisões pela tag."),
    ("Modo de câmera",
     "Use o botão 'Câmera' no topo para trocar entre Perspectiva, Top-Down e Side-Scroller."),
    ("Testar o jogo",
     "Clique em PLAY para testar. Clique em STOP para voltar ao editor. Posições são restauradas."),
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
        self.btn_tree_up   = GuiButton(200, TREE_Y + 20,                 26, 20, "▲", _S, _SH)
        self.btn_tree_down = GuiButton(200, TREE_Y + lay._tree_h - 2,   26, 20, "▼", _S, _SH)

        # ── Ângulo de luz ────────────────────────────────────────────────────
        self.btn_light_angle_dec = GuiButton(LEFT_PADDING,        lay.light_section_y, 38, ROW_H_SMALL, "<", _S, _SH)
        self.btn_light_angle_inc = GuiButton(LEFT_PANEL_W - 50,   lay.light_section_y, 38, ROW_H_SMALL, ">", _S, _SH)

        # ── Barra superior ───────────────────────────────────────────────────
        self.btn_menu_file   = GuiButton( 10, 2, 52, 26, "File",   T.BG, T.SURFACE)
        self.btn_menu_view   = GuiButton( 66, 2, 52, 26, "View",   T.BG, T.SURFACE)
        self.btn_menu_window = GuiButton(122, 2, 72, 26, "Window", T.BG, T.SURFACE)

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
                    data["_file"] = os.path.join(demos_dir, fname)
                    templates.append(data)
                except Exception:
                    pass
        return templates

    def _load_template(self, tpl: Dict) -> None:
        self.history.push(self)
        for obj in list(self.editable_objects):
            self._remove_go(obj); obj.destroy()
        self.editable_objects.clear()
        self.selected_index = -1
        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
        for item in tpl.get("objects", []):
            go = GameObject()
            go.name               = item["name"]
            go.transform.position = np.array(item["position"], np.float32)
            go.transform.rotation = np.array(item["rotation"], np.float32)
            go.transform.scale    = np.array(item["scale"],    np.float32)
            go.mesh_type          = item.get("shape", "Cube")
            go.is_static          = item.get("is_static", False)
            go.use_physics        = item.get("use_physics", True)
            go.initial_velocity_y = item.get("initial_velocity_y", 0.0)
            go.script_path        = item.get("script_path", "")
            go.tag                = item.get("tag", "")
            count_map = {"Cube": "cube_count", "Pyramid": "pyramid_count",
                         "Sphere": "sphere_count", "Plane": "plane_count",
                         "Capsule": "capsule_count", "Camera": "camera_count", "Light": "light_count"}
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)
        for item, go in zip(tpl.get("objects", []), self.editable_objects):
            parent_name = item.get("parent_name")
            if parent_name:
                parent_obj = next((o for o in self.editable_objects if o.name == parent_name), None)
                if parent_obj:
                    parent_obj.add_child(go)
        if self.editable_objects:
            self.selected_index = 0
        self.showing_templates = False
        self._tree_scroll = 0
        self._cancel_rename()
        self._notify(f"Template '{tpl.get('_template_name', '')}' carregado!", "success")

    def _set_camera_mode(self, mode_name: str) -> None:
        preset = CAMERA_MODE_PRESETS.get(mode_name, CAMERA_MODE_PRESETS["Perspectiva"])
        self.camera_controller.target_yaw      = preset["yaw"]
        self.camera_controller.target_pitch    = preset["pitch"]
        self.camera_controller.target_distance = preset["dist"]
        self.btn_camera_mode.text = f"Camera: {mode_name[:5]}"

    # -----------------------------------------------------------------------
    def _add_go(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    def _remove_go(self, go: GameObject) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)

    def _snap(self, v: np.ndarray) -> np.ndarray:
        if self.snap_enabled:
            return np.round(v / SNAP_SIZE) * SNAP_SIZE
        return v

    # -----------------------------------------------------------------------
    def _make_mesh(self, shape: str, color: tuple):
        from editor.mesh_factory import create_plane_mesh, create_capsule_mesh
        if shape == "Cube":     return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)
        elif shape == "Pyramid": return MeshRenderer3D(create_pyramid_mesh(1.0), color=color)
        elif shape == "Sphere":  return MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color)
        elif shape == "Plane":   return MeshRenderer3D(create_plane_mesh(size=2.0, subdivisions=2), color=color)
        elif shape == "Capsule": return MeshRenderer3D(create_capsule_mesh(radius=0.4, height=1.0, rings=8, sectors=10), color=color)
        elif shape == "Camera":  return MeshRenderer3D(create_pyramid_mesh(0.5), color=color)
        elif shape == "Light":   return MeshRenderer3D(create_sphere_mesh(radius=0.25, rings=6, sectors=6), color=color)
        else:                    return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)

    def spawn_object(self, shape: str) -> None:
        self.history.push(self)
        go = GameObject()
        go.transform.position = np.array([0.0, 0.0, 1.5], dtype=np.float32)
        go.mesh_type          = shape
        go.is_static          = False
        go.use_physics        = True
        go.initial_velocity_y = 0.0
        go.script_path        = ""
        go.tag                = ""
        default_colors = {
            "Cube":    (  0, 110, 220), "Pyramid": (220,  60,  20),
            "Sphere":  (100,  40, 180), "Plane":   ( 60, 160,  80),
            "Capsule": (200, 140,   0), "Camera":  ( 50, 200, 200),
            "Light":   (255, 230,  50),
        }
        default_names = {
            "Cube":    "Bloco",   "Pyramid": "Piramide", "Sphere":  "Bolinha",
            "Plane":   "Plano",   "Capsule": "Capsula",  "Camera":  "Camera",
            "Light":   "Luz",
        }
        count_map = {
            "Cube": "cube_count", "Pyramid": "pyramid_count", "Sphere": "sphere_count",
            "Plane": "plane_count", "Capsule": "capsule_count",
            "Camera": "camera_count", "Light": "light_count",
        }
        attr = count_map.get(shape, "cube_count")
        setattr(self, attr, getattr(self, attr) + 1)
        go.name = f"{default_names.get(shape, shape)}_{getattr(self, attr)}"
        color   = default_colors.get(shape, (200, 200, 200))
        go.add_component(self._make_mesh(shape, color))
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll_to(self.selected_index)
        self._notify(f"{go.name} adicionado", "success")

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
        self.history.push(self)
        go = self.editable_objects.pop(self.selected_index)
        name = go.name
        self._remove_go(go)
        go.destroy()
        self.selected_index = -1 if not self.editable_objects else max(0, self.selected_index - 1)
        self._notify(f"'{name}' excluído", "info")

    def clone_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
        self.history.push(self)
        src = self.editable_objects[self.selected_index]
        go = GameObject()
        go.mesh_type          = getattr(src, "mesh_type", "Cube")
        go.name               = src.name + "_Clone"
        go.is_static          = getattr(src, "is_static", False)
        go.use_physics        = getattr(src, "use_physics", True)
        go.initial_velocity_y = getattr(src, "initial_velocity_y", 0.0)
        go.script_path        = getattr(src, "script_path", "")
        go.tag                = getattr(src, "tag", "")
        go.transform.position = src.transform.position.copy() + np.array([0.5, 0.0, 0.5])
        go.transform.rotation = src.transform.rotation.copy()
        go.transform.scale    = src.transform.scale.copy()
        renderer = src.get_component(MeshRenderer3D)
        color    = renderer.color if renderer else (200, 200, 200)
        go.add_component(self._make_mesh(go.mesh_type, color))
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll_to(self.selected_index)
        self._notify(f"'{go.name}' clonado", "success")

    # -----------------------------------------------------------------------
    def _build_flat_tree(self) -> List[Tuple[GameObject, int]]:
        flat = []
        roots = [obj for obj in self.editable_objects if getattr(obj, "parent", None) is None]
        def traverse(obj, depth):
            flat.append((obj, depth))
            for child in self.editable_objects:
                if getattr(child, "parent", None) == obj:
                    traverse(child, depth + 1)
        for r in roots:
            traverse(r, 0)
        flat_objs = [f[0] for f in flat]
        for obj in self.editable_objects:
            if obj not in flat_objs:
                flat.append((obj, 0))
        return flat

    def _start_rename(self, idx: int) -> None:
        if not (0 <= idx < len(self.editable_objects)): return
        self._rename_index = idx
        self._rename_text  = self.editable_objects[idx].name
        self._rename_blink = 0.0
        self._rename_cursor_on = True

    def _commit_rename(self) -> None:
        if self._rename_index >= 0 and self._rename_text.strip():
            self.editable_objects[self._rename_index].name = self._rename_text.strip()
        self._rename_index = -1
        self._rename_text  = ""

    def _cancel_rename(self) -> None:
        self._rename_index = -1
        self._rename_text  = ""

    def _tree_scroll_to(self, idx: int) -> None:
        if idx < 0: return
        if idx < self._tree_scroll:
            self._tree_scroll = idx
        elif idx >= self._tree_scroll + self._lay.tree_max_vis:
            self._tree_scroll = idx - self._lay.tree_max_vis + 1

    def _max_scroll(self) -> int:
        return max(0, len(self.editable_objects) - self._lay.tree_max_vis)

    # -----------------------------------------------------------------------
    def save_scene(self) -> None:
        data = {"objects": []}
        for obj in self.editable_objects:
            r = obj.get_component(MeshRenderer3D)
            data["objects"].append({
                "name":               obj.name,
                "shape":              getattr(obj, "mesh_type", "Cube"),
                "position":           obj.transform.position.tolist(),
                "rotation":           obj.transform.rotation.tolist(),
                "scale":              obj.transform.scale.tolist(),
                "color":              list(r.color) if r else [200, 200, 200],
                "is_static":          getattr(obj, "is_static", False),
                "use_physics":        getattr(obj, "use_physics", True),
                "initial_velocity_y": getattr(obj, "initial_velocity_y", 0.0),
                "script_path":        getattr(obj, "script_path", ""),
                "tag":                getattr(obj, "tag", ""),
                "parent_name":        obj.parent.name if obj.parent else None,
            })
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            self._notify("Cena salva com sucesso!", "success")
        except Exception as e:
            self._notify(f"Erro ao salvar: {e}", "error")

    def load_scene(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        if not os.path.exists(path):
            self._notify("Nenhuma cena salva encontrada.", "error"); return
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            self._notify(f"Erro ao carregar: {e}", "error"); return
        self.history.push(self)
        for obj in list(self.editable_objects):
            self._remove_go(obj); obj.destroy()
        self.editable_objects.clear()
        self.selected_index = -1
        self.cube_count = self.pyramid_count = self.sphere_count = self.plane_count = self.capsule_count = self.camera_count = self.light_count = 0
        for item in data.get("objects", []):
            go = GameObject()
            go.name               = item["name"]
            go.transform.position = np.array(item["position"], np.float32)
            go.transform.rotation = np.array(item["rotation"], np.float32)
            go.transform.scale    = np.array(item["scale"],    np.float32)
            go.mesh_type          = item.get("shape", "Cube")
            go.is_static          = item.get("is_static", False)
            go.use_physics        = item.get("use_physics", True)
            go.initial_velocity_y = item.get("initial_velocity_y", 0.0)
            go.script_path        = item.get("script_path", "")
            go.tag                = item.get("tag", "")
            count_map = {"Cube": "cube_count", "Pyramid": "pyramid_count", "Sphere": "sphere_count",
                         "Plane": "plane_count", "Capsule": "capsule_count",
                         "Camera": "camera_count", "Light": "light_count"}
            attr = count_map.get(go.mesh_type, "cube_count")
            setattr(self, attr, getattr(self, attr) + 1)
            color = tuple(item["color"])
            go.add_component(self._make_mesh(go.mesh_type, color))
            self._add_go(go)
            self.editable_objects.append(go)
        for item, go in zip(data.get("objects", []), self.editable_objects):
            parent_name = item.get("parent_name")
            if parent_name:
                parent_obj = next((o for o in self.editable_objects if o.name == parent_name), None)
                if parent_obj:
                    parent_obj.add_child(go)
        if self.editable_objects:
            self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll = 0
        self._cancel_rename()
        self._notify("Cena carregada!", "success")

    # -----------------------------------------------------------------------
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
        for btn in [
            self.btn_toggle_static, self.btn_toggle_physics,
            self.btn_vel_dec, self.btn_new_script,
            self.btn_edit_script, self.btn_script_help,
            self.btn_clone, self.btn_prev_parent, self.btn_prev_tag,
            self.btn_prev_script,
        ]:
            btn.x = rx

        # Inspector direita (botões '>')
        self.btn_vel_inc.x         = rx + 145
        self.btn_next_script.x     = lay.insp_btn_right(28)
        self.btn_internal_editor.x = rx + 110
        self.btn_next_parent.x     = lay.insp_btn_right(28)
        self.btn_next_tag.x        = lay.insp_btn_right(28)

        # Botões de cor
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
                                      "EDIT MODE",       T.ACCENT)
            self._draw_viewport_badge(screen, lay.viewport_game_rect.x + 8,  TOP_BAR_H + 8,
                                      "GAME VIEW (PLAY)", T.SUCCESS)
        else:
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
                                      "EDIT MODE", T.ACCENT)

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

        self._draw_dropdowns(screen)

        if self._is_dragging_tree and self._drag_tree_src:
            mx, my = pygame.mouse.get_pos()
            label = f"Mover {self._drag_tree_src.name} para..."
            pygame.draw.rect(screen, T.BTN_ACTIVE, (mx + 15, my + 5, 200, 24), border_radius=4)
            screen.blit(self.font_body.render(label, True, T.TEXT_PRIMARY), (mx + 22, my + 9))

    # -----------------------------------------------------------------------
    # Draw helpers
    # -----------------------------------------------------------------------
    def _draw_viewport_badge(self, screen, x, y, text, color):
        """Badge colorido sobre a viewport (EDIT MODE / GAME VIEW)."""
        surf = self.font_btn.render(text, True, color)
        w = surf.get_width() + 14
        pygame.draw.rect(screen, T.PANEL, (x, y, w, 18), border_radius=3)
        pygame.draw.rect(screen, color,   (x, y, w, 18), 1, border_radius=3)
        screen.blit(surf, (x + 7, y + 2))

    def _draw_game_view(self, screen: pygame.Surface) -> None:
        """Renderiza a game view (lado direito no modo play)."""
        lay  = self._lay
        rect = lay.viewport_game_rect
        pygame.draw.rect(screen, T.BG, rect)
        # Placeholder — em versão futura: renderização de câmera de jogo separada
        label = self.font_body.render("[Game View]", True, T.TEXT_MUTED)
        screen.blit(label, (
            rect.x + (rect.width  - label.get_width())  // 2,
            rect.y + (rect.height - label.get_height()) // 2,
        ))

    def _draw_status_bar(self, screen: pygame.Surface) -> None:
        """Barra de status inferior com feedback das últimas ações."""
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL,  lay.status_bar_rect)
        pygame.draw.line(screen, T.BORDER,
                         (0, lay.status_bar_rect.y),
                         (lay.screen_w, lay.status_bar_rect.y), 1)

        info = (f"  {len(self.editable_objects)} objeto(s)   "
                f"Grade: {'ON' if self.snap_enabled else 'OFF'}   "
                f"Hist: {len(self.history._undo)} undo / {len(self.history._redo)} redo")
        screen.blit(self.font_section.render(info, True, T.TEXT_MUTED),
                    (8, lay.status_text_y()))

        if self._status_timer > 0 and self._status_msg:
            alpha = min(1.0, self._status_timer)
            kind_colors = {"info": T.ACCENT, "success": T.SUCCESS, "error": T.ERROR}
            col   = kind_colors.get(getattr(self, "_status_kind", "info"), T.ACCENT)
            faded = T.alpha_blend(col, alpha, T.PANEL)
            surf  = self.font_section.render(f"● {self._status_msg}", True, faded)
            screen.blit(surf, (lay.status_center_x(surf.get_width()), lay.status_text_y()))

    def _draw_gizmo(self, screen: pygame.Surface) -> None:
        if self.selected_index < 0 or self.play_mode or not self.gizmo_mode:
            return
        sel = self.editable_objects[self.selected_index]
        P   = sel.transform.position
        ext = 1.2
        ex  = P + np.array([ext, 0.0, 0.0], np.float32)
        ey  = P + np.array([0.0, ext, 0.0], np.float32)
        ez  = P + np.array([0.0, 0.0, ext], np.float32)
        verts = np.array([P, ex, ey, ez], np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        near = self.camera_comp.near
        if not all(d > near for d in depths): return
        vw, vh = self.camera_comp.viewport_width,  self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x,      self.camera_comp.viewport_y
        def ts(i): return int(vx + (ndc[i, 0] + 1) * vw / 2), int(vy + (-ndc[i, 1] + 1) * vh / 2)
        c, px, py, pz = ts(0), ts(1), ts(2), ts(3)
        self.gizmo_screen_points = {'x': px, 'y': py, 'z': pz}
        self.gizmo_screen_center = c

        def draw_triangle(surface, color, pt, center):
            dx = pt[0] - center[0]; dy = pt[1] - center[1]
            dist = np.hypot(dx, dy)
            if dist > 0:
                ux, uy = dx / dist, dy / dist
                px_, py_ = -uy, ux
                p1 = (pt[0] + ux * 8, pt[1] + uy * 8)
                p2 = (pt[0] - ux * 8 + px_ * 6, pt[1] - uy * 8 + py_ * 6)
                p3 = (pt[0] - ux * 8 - px_ * 6, pt[1] - uy * 8 - py_ * 6)
                pygame.draw.polygon(surface, color, [p1, p2, p3])

        if self.gizmo_mode == "rotate":
            for pts_fn, col in [
                (lambda t: P + np.array([0.8*np.cos(t), 0, 0.8*np.sin(t)], np.float32), T.GIZMO_Y),
                (lambda t: P + np.array([0, 0.8*np.cos(t), 0.8*np.sin(t)], np.float32), T.GIZMO_X),
                (lambda t: P + np.array([0.8*np.cos(t), 0.8*np.sin(t), 0], np.float32), T.GIZMO_Z),
            ]:
                ring = np.array([pts_fn(t) for t in np.linspace(0, 2*np.pi, 20)], np.float32)
                rn, rd = project_vertices(ring, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                pts = [(int(vx+(rn[k,0]+1)*vw/2), int(vy+(-rn[k,1]+1)*vh/2))
                       for k in range(len(ring)) if rd[k] > near]
                if len(pts) > 1: pygame.draw.lines(screen, col, True, pts, 2)
            draw_triangle(screen, T.GIZMO_X, px, c)
            draw_triangle(screen, T.GIZMO_Y, py, c)
            draw_triangle(screen, T.GIZMO_Z, pz, c)
        else:
            pygame.draw.line(screen, T.GIZMO_X, c, px, 3)
            pygame.draw.line(screen, T.GIZMO_Y, c, py, 3)
            pygame.draw.line(screen, T.GIZMO_Z, c, pz, 3)
            if self.gizmo_mode == "translate":
                for pt, col in [(px, T.GIZMO_X), (py, T.GIZMO_Y), (pz, T.GIZMO_Z)]:
                    pygame.draw.circle(screen, col, pt, 7)
            elif self.gizmo_mode == "scale":
                for pt, col in [(px, T.GIZMO_X), (py, T.GIZMO_Y), (pz, T.GIZMO_Z)]:
                    pygame.draw.rect(screen, col, (pt[0]-6, pt[1]-6, 12, 12))
                pygame.draw.circle(screen, T.GIZMO_W, c, 6)

    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL, lay.left_panel_rect)
        pygame.draw.line(screen, T.BORDER,
                         (LEFT_PANEL_W, TOP_BAR_H),
                         (LEFT_PANEL_W, lay.screen_h), 1)

        # ── Seção: Formas ──
        SectionHeader(LEFT_PADDING, ADD_SECTION_Y, LEFT_PANEL_W - 16, "Adicionar").draw(screen, self.font_section)
        for btn in [self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
                    self.btn_add_plane, self.btn_add_capsule, self.btn_add_camera, self.btn_add_light]:
            btn.draw(screen, self.font_btn)

        # ── Seção: Gizmo ──
        SectionHeader(LEFT_PADDING, GIZMO_SECTION_Y, LEFT_PANEL_W - 16, "Transformar").draw(screen, self.font_section)
        for btn, mode in [(self.btn_mode_translate, "translate"),
                          (self.btn_mode_rotate,    "rotate"),
                          (self.btn_mode_scale,     "scale")]:
            active = (self.gizmo_mode == mode)
            btn.bg_color    = T.BTN_ACTIVE       if active else T.BTN_GIZMO
            btn.hover_color = T.BTN_ACTIVE_HOVER if active else T.BTN_GIZMO_HOVER
            btn.draw(screen, self.font_btn)

        # ── Snap + Templates ──
        self.btn_snap.text      = f"Grade: {'ON  (G)' if self.snap_enabled else 'OFF (G)'}"
        self.btn_snap.bg_color  = (25, 90, 58) if self.snap_enabled else T.BTN_SECONDARY
        self.btn_snap.draw(screen, self.font_btn)
        self.btn_templates.draw(screen, self.font_btn)

        # ── Seção: Cena (Outliner) ──
        SectionHeader(LEFT_PADDING, TREE_Y - 14, LEFT_PANEL_W - 16, "Objetos da Cena").draw(screen, self.font_section)

        tree_rect = pygame.Rect(LEFT_PADDING, TREE_Y, 184, lay.tree_h)
        pygame.draw.rect(screen, T.BG,     tree_rect, border_radius=4)
        pygame.draw.rect(screen, T.BORDER, tree_rect, 1, border_radius=4)

        flat_tree = self._build_flat_tree()
        total     = len(flat_tree)
        max_s     = self._max_scroll()
        self._tree_scroll = min(self._tree_scroll, max_s)

        for slot_i in range(lay.tree_max_vis):
            obj_i = self._tree_scroll + slot_i
            if obj_i >= total: break
            obj, depth = flat_tree[obj_i]
            sel = (0 <= self.selected_index < len(self.editable_objects)
                   and self.editable_objects[self.selected_index] == obj)

            ry  = TREE_Y + slot_i * TREE_ROW_H
            row = pygame.Rect(LEFT_PADDING + 1, ry, 182, TREE_ROW_H - 1)

            if sel:
                pygame.draw.rect(screen, T.ACCENT_BG, row, border_radius=3)
                pygame.draw.rect(screen, T.ACCENT,    row, 1, border_radius=3)
            else:
                mx, my = pygame.mouse.get_pos()
                if row.collidepoint(mx, my):
                    pygame.draw.rect(screen, T.SURFACE, row, border_radius=3)

            indent   = min(depth, 4) * 10
            icon     = _SHAPE_ICON.get(getattr(obj, "mesh_type", "Cube"), "▣")
            icon_col = T.ACCENT if sel else T.TEXT_MUTED
            screen.blit(self.font_section.render(icon, True, icon_col), (18 + indent, ry + 7))

            if self._rename_index >= 0 and self.editable_objects[self._rename_index] == obj:
                pygame.draw.rect(screen, T.SURFACE_2, (32 + indent, ry + 3, 152 - indent, TREE_ROW_H - 6), border_radius=2)
                pygame.draw.rect(screen, T.ACCENT,    (32 + indent, ry + 3, 152 - indent, TREE_ROW_H - 6), 1, border_radius=2)
                display = self._rename_text + ("|" if self._rename_cursor_on else "")
                screen.blit(self.font_body.render(display, True, T.TEXT_PRIMARY), (35 + indent, ry + 5))
            else:
                label   = obj.name
                max_len = 18 - (indent // 10) * 2
                if len(label) > max_len: label = label[:max(5, max_len - 2)] + ".."
                screen.blit(self.font_body.render(label, True, T.TEXT_PRIMARY), (32 + indent, ry + 5))
                tag = getattr(obj, "tag", "")
                if tag:
                    ts = self.font_section.render(tag, True, T.WARNING)
                    screen.blit(ts, (155 - ts.get_width(), ry + 7))

        # Scrollbar
        if total > lay.tree_max_vis:
            bar_h = max(16, lay.tree_h * lay.tree_max_vis // max(total, 1))
            bar_y = TREE_Y + (lay.tree_h - bar_h) * self._tree_scroll // max(max_s, 1)
            pygame.draw.rect(screen, T.BORDER, (196, bar_y, 4, bar_h), border_radius=2)
            self.btn_tree_up.draw(screen, self.font_btn)
            self.btn_tree_down.draw(screen, self.font_btn)

        # Undo / Redo / Delete
        Divider(LEFT_PADDING, TREE_Y + lay.tree_h + 8, LEFT_PANEL_W - 24).draw(screen)
        self.btn_undo.bg_color    = T.BTN_ACTIVE       if self.history.can_undo else T.BTN_SECONDARY
        self.btn_redo.bg_color    = T.BTN_ACTIVE       if self.history.can_redo else T.BTN_SECONDARY
        self.btn_undo.hover_color = T.BTN_ACTIVE_HOVER if self.history.can_undo else T.BTN_SECONDARY_HOVER
        self.btn_redo.hover_color = T.BTN_ACTIVE_HOVER if self.history.can_redo else T.BTN_SECONDARY_HOVER
        self.btn_undo.draw(screen, self.font_btn)
        self.btn_redo.draw(screen, self.font_btn)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen, self.font_btn)

        # ── Seção: Luz ──
        Divider(LEFT_PADDING, lay.light_section_y - 18, LEFT_PANEL_W - 24).draw(screen)
        SectionHeader(LEFT_PADDING, lay.light_section_y - 14, LEFT_PANEL_W - 16, "Direção da Luz").draw(screen, self.font_section)
        self.btn_light_angle_dec.draw(screen, self.font_btn)
        angle_surf = self.font_xyz.render(f"{int(self.light_angle)}°", True, T.TEXT_PRIMARY)
        screen.blit(angle_surf, (60 + (100 - angle_surf.get_width()) // 2, lay.light_section_y + 2))
        self.btn_light_angle_inc.draw(screen, self.font_btn)

    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL, lay.top_bar_rect)
        pygame.draw.line(screen, T.BORDER, (0, TOP_BAR_H), (lay.screen_w, TOP_BAR_H), 1)

        logo = self.font_body.render("Zennity", True, T.ACCENT)
        screen.blit(logo, (8, 7))
        pygame.draw.line(screen, T.BORDER, (70, 4), (70, 26), 1)

        self.btn_menu_file.draw(screen,   self.font_btn)
        self.btn_menu_view.draw(screen,   self.font_btn)
        self.btn_menu_window.draw(screen, self.font_btn)

        if self.play_mode:
            self.btn_play_pause.bg_color    = T.BTN_DANGER
            self.btn_play_pause.hover_color = T.BTN_DANGER_HOVER
            self.btn_play_pause.text        = "■  STOP"
        else:
            self.btn_play_pause.bg_color    = T.BTN_PRIMARY
            self.btn_play_pause.hover_color = T.BTN_PRIMARY_HOVER
            self.btn_play_pause.text        = "▶  PLAY"
        self.btn_play_pause.draw(screen, self.font_btn)

        undo_col = T.ACCENT if self.history.can_undo else T.TEXT_FAINT
        redo_col = T.ACCENT if self.history.can_redo else T.TEXT_FAINT
        screen.blit(self.font_btn.render(f"↩ {len(self.history._undo)}", True, undo_col), (lay.screen_w - 120, 8))
        screen.blit(self.font_btn.render(f"↪ {len(self.history._redo)}", True, redo_col), (lay.screen_w -  68, 8))

    def _draw_dropdowns(self, screen: pygame.Surface) -> None:
        if not self._active_dropdown: return
        if self._active_dropdown == "file":
            opts = ["Novo Scene", "Salvar", "Carregar", "Sair"]
            rx, ry, rw = 10, TOP_BAR_H, 130
        elif self._active_dropdown == "view":
            grade_str = "Desativar Grade" if self.snap_enabled else "Ativar Grade"
            opts = ["Camera: Persp", "Camera: Top", "Camera: Side", grade_str, "Templates"]
            rx, ry, rw = 66, TOP_BAR_H, 155
        elif self._active_dropdown == "window":
            fs_str = "Modo Janela" if getattr(self.engine, "is_fullscreen", False) else "Tela Cheia"
            opts = [fs_str + " (F11)", "Guia de Ajuda"]
            rx, ry, rw = 122, TOP_BAR_H, 165
        else:
            return
        rh = len(opts) * 28
        pygame.draw.rect(screen, T.SURFACE, (rx, ry, rw, rh), border_radius=4)
        pygame.draw.rect(screen, T.BORDER,  (rx, ry, rw, rh), 1, border_radius=4)
        mx, my = pygame.mouse.get_pos()
        for i, opt in enumerate(opts):
            row_rect = pygame.Rect(rx + 1, ry + i * 28 + 1, rw - 2, 26)
            if row_rect.collidepoint(mx, my):
                pygame.draw.rect(screen, T.BTN_ACTIVE, row_rect, border_radius=3)
            screen.blit(self.font_body.render(opt, True, T.TEXT_PRIMARY), (rx + 10, ry + i * 28 + 6))

    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        lay = self._lay
        pygame.draw.rect(screen, T.PANEL, lay.right_panel_rect)
        pygame.draw.line(screen, T.BORDER,
                         (lay.right_x, TOP_BAR_H),
                         (lay.right_x, lay.screen_h), 1)

        if not (0 <= self.selected_index < len(self.editable_objects)):
            empty_surf = self.font_body.render("Nenhum objeto selecionado", True, T.TEXT_FAINT)
            screen.blit(empty_surf,
                        (lay.right_x + (RIGHT_PANEL_W - empty_surf.get_width()) // 2, 80))
            return

        sel = self.editable_objects[self.selected_index]
        pos, rot, sc = sel.transform.position, sel.transform.rotation, sel.transform.scale
        rx = lay.inspector_x()

        # ── Cabeçalho ──
        name_surf = self.font_xyz.render(sel.name, True, T.TEXT_PRIMARY)
        icon      = _SHAPE_ICON.get(getattr(sel, "mesh_type", "Cube"), "▣")
        icon_surf = self.font_xyz.render(icon, True, T.ACCENT)
        screen.blit(icon_surf, (rx, INSP_HEADER_Y))
        screen.blit(name_surf, (rx + 20, INSP_HEADER_Y))
        Divider(rx, INSP_HEADER_Y + 20, INSPECTOR_W).draw(screen)

        # ── Física ──
        SectionHeader(rx, INSP_PHYSICS_Y, INSPECTOR_W, "Física").draw(screen, self.font_section)
        self.btn_toggle_static.draw(screen, self.font_btn)
        if getattr(sel, "is_static", False):
            pygame.draw.rect(screen, T.ACCENT, (rx + 3, INSP_PHYSICS_Y - 9, 14, 14))
        else:
            pygame.draw.rect(screen, T.BORDER, (rx + 3, INSP_PHYSICS_Y - 9, 14, 14), border_radius=3)
        screen.blit(self.font_body.render("Estático",  True, T.TEXT_PRIMARY), (rx + 28, INSP_PHYSICS_Y - 10))

        self.btn_toggle_physics.draw(screen, self.font_btn)
        if getattr(sel, "use_physics", True):
            pygame.draw.rect(screen, T.ACCENT, (rx + 3, INSP_PHYSICS_Y + 21, 14, 14))
        screen.blit(self.font_body.render("Gravidade", True, T.TEXT_PRIMARY), (rx + 28, INSP_PHYSICS_Y + 20))

        screen.blit(self.font_section.render("IMPULSO VERTICAL", True, T.TEXT_MUTED),
                    (rx, INSP_PHYSICS_Y + 50))
        self.btn_vel_dec.draw(screen, self.font_btn)
        val_surf = self.font_xyz.render(f"{sel.initial_velocity_y:+.1f} m/s", True, T.TEXT_PRIMARY)
        screen.blit(val_surf, (rx + 48, INSP_PHYSICS_Y + 73))
        self.btn_vel_inc.draw(screen, self.font_btn)

        Divider(rx, INSP_PHYSICS_Y + 100, INSPECTOR_W).draw(screen)

        # ── Scripts ──
        SectionHeader(rx, INSP_SCRIPT_Y, INSPECTOR_W, "Comportamento").draw(screen, self.font_section)
        self.btn_prev_script.draw(screen, self.font_btn)
        self.btn_next_script.draw(screen, self.font_btn)
        self.btn_new_script.draw(screen, self.font_btn)
        self.btn_edit_script.draw(screen, self.font_btn)
        self.btn_internal_editor.draw(screen, self.font_btn)
        self.btn_script_help.draw(screen, self.font_btn)

        script_name = getattr(sel, "script_path", "") or "Nenhum"
        if len(script_name) > 22: script_name = script_name[-22:]
        screen.blit(self.font_body.render(script_name, True, T.TEXT_PRIMARY),
                    (rx + 32, INSP_SCRIPT_Y + 24))

        Divider(rx, INSP_COLOR_Y, INSPECTOR_W).draw(screen)

        # ── Cores ──
        SectionHeader(rx, INSP_COLOR_Y + 4, INSPECTOR_W, "Cor").draw(screen, self.font_section)
        for btn in self.btn_colors:
            btn.draw(screen, self.font_btn)
        r_comp = sel.get_component(MeshRenderer3D)
        if r_comp:
            cur_col = r_comp.color
            pygame.draw.rect(screen, cur_col,   (rx, INSP_COLOR_Y + 56, INSPECTOR_W, 12), border_radius=3)
            pygame.draw.rect(screen, T.BORDER,  (rx, INSP_COLOR_Y + 56, INSPECTOR_W, 12), 1, border_radius=3)

        Divider(rx, INSP_CLONE_Y - 8, INSPECTOR_W).draw(screen)

        # ── Clone ──
        self.btn_clone.draw(screen, self.font_btn)

        Divider(rx, INSP_HIER_Y - 4, INSPECTOR_W).draw(screen)

        # ── Hierarquia ──
        SectionHeader(rx, INSP_HIER_Y, INSPECTOR_W, "Pai (Hierarquia)").draw(screen, self.font_section)
        self.btn_prev_parent.draw(screen, self.font_btn)
        self.btn_next_parent.draw(screen, self.font_btn)
        parent_name = sel.parent.name if getattr(sel, "parent", None) else "(raiz)"
        screen.blit(self.font_body.render(parent_name, True, T.TEXT_PRIMARY),
                    (rx + 32, INSP_HIER_Y + 5))

        Divider(rx, INSP_TAG_Y - 4, INSPECTOR_W).draw(screen)

        # ── Tag ──
        SectionHeader(rx, INSP_TAG_Y, INSPECTOR_W, "Tag").draw(screen, self.font_section)
        self.btn_prev_tag.draw(screen, self.font_btn)
        self.btn_next_tag.draw(screen, self.font_btn)
        tag_name = getattr(sel, "tag", "") or "(sem tag)"
        screen.blit(self.font_body.render(tag_name, True, T.TEXT_PRIMARY),
                    (rx + 32, INSP_TAG_Y + 5))

        Divider(rx, INSP_TRANSFORM_Y - 4, INSPECTOR_W).draw(screen)

        # ── Transform ──
        SectionHeader(rx, INSP_TRANSFORM_Y, INSPECTOR_W, "Transform").draw(screen, self.font_section)
        labels = [("X", T.GIZMO_X), ("Y", T.GIZMO_Y), ("Z", T.GIZMO_Z)]
        for row_i, (label, col) in enumerate(labels):
            y_base = INSP_TRANSFORM_Y + 16 + row_i * 44
            screen.blit(self.font_section.render("POS", True, T.TEXT_MUTED), (rx, y_base))
            screen.blit(self.font_section.render(label,  True, col),          (rx + 28, y_base))
            screen.blit(self.font_xyz.render(f"{pos[row_i]:+.2f}", True, T.TEXT_PRIMARY), (rx + 42, y_base))
            screen.blit(self.font_section.render("ESC", True, T.TEXT_MUTED), (rx + 90, y_base))
            screen.blit(self.font_xyz.render(f"{rot[row_i]:+.1f}°", True, T.TEXT_PRIMARY), (rx + 114, y_base))
            screen.blit(self.font_section.render("TAM", True, T.TEXT_MUTED), (rx, y_base + 20))
            screen.blit(self.font_xyz.render(f"{sc[row_i]:+.2f}",  True, T.TEXT_PRIMARY), (rx + 28, y_base + 20))

    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        """Mini widget XYZ no canto superior direito da viewport."""
        lay = self._lay
        wx = lay.viewport_rect.right - 60
        wy = TOP_BAR_H + 8
        labels = [("X", T.GIZMO_X), ("Y", T.GIZMO_Y), ("Z", T.GIZMO_Z)]
        for i, (label, col) in enumerate(labels):
            screen.blit(self.font_section.render(label, True, col), (wx + i * 20, wy))
