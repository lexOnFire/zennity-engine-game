"""
Cena principal do editor 3D da Zennity Engine.
Melhorias nesta versão:
  - Janela 1400x800 — viewport maior, sem sobreposição
  - Painel esquerdo 260px, painel direito 280px
  - Tree/outliner com mais espaço e scroll
  - Novas formas: Plano (Plane) e Cápsula (Capsule)
  - Play/Stop com serialização/restauração completa
  - Câmera e luz como controles dedicados
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

from .gui import GuiButton
from .mesh_factory import (
    create_pyramid_mesh,
    create_sphere_mesh,
    create_plane_mesh,
    create_capsule_mesh,
)
from .camera_controller import OrbitCameraController
from .physics_sim import PhysicsSim
from .script_manager import ScriptManager
from .code_editor import CodeEditor
from .history import History

_IDENTITY = np.eye(4, dtype=np.float32)

# ── Layout ────────────────────────────────────────────────────────────────────
WIN_W  = 1400
WIN_H  = 800

_LEFT_W   = 260          # largura painel esquerdo
_RIGHT_W  = 280          # largura painel direito
_RIGHT_X  = WIN_W - _RIGHT_W   # x inicial painel direito  (1120)
_VP_X     = _LEFT_W             # viewport começa após painel esq
_VP_W     = _RIGHT_X - _VP_X   # largura do viewport  (860)
_VP_Y     = 50                  # abaixo da barra de topo
_VP_H     = WIN_H - _VP_Y       # altura viewport (750)

_TOP_H    = _VP_Y        # altura barra de topo

# Tree/outliner — posicionada dentro do painel esquerdo
_TREE_LABEL_Y = 200      # y do título "OBJETOS DA CENA"
_TREE_Y       = 220      # y topo da caixa de lista
_TREE_H       = 260      # altura da caixa (cabe ~13 itens de 20px)
_TREE_ROW_H   = 22
_TREE_MAX_VIS = _TREE_H // _TREE_ROW_H

# Modos de câmera
CAMERA_MODES = ["Perspectiva", "Top-Down", "Side-Scroller"]

CAMERA_MODE_PRESETS = {
    "Perspectiva":    {"yaw": 0.0,   "pitch": 25.0, "dist": 6.0},
    "Top-Down":       {"yaw": 0.0,   "pitch": 89.9, "dist": 8.0},
    "Side-Scroller":  {"yaw": 90.0,  "pitch": 5.0,  "dist": 7.0},
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
    (200, 200, 200), (220, 50, 50), (50, 170, 50),
    (50, 100, 220),  (240, 200, 0), (200, 50, 200),
]

TAG_OPTIONS = ["", "player", "inimigo", "perigoso", "coletavel", "chao"]

HELP_LINES = [
    "Atalhos de teclado:",
    "  Ctrl+Z           Desfazer (Undo)",
    "  Ctrl+Shift+Z     Refazer (Redo)",
    "  Ctrl+D           Clonar objeto selecionado",
    "  Delete           Excluir objeto selecionado",
    "  G                Ativar/desativar snap de grade (0.5)",
    "  F2               Renomear objeto selecionado",
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
     "Clique em '+ Cubo', '+ Pirâm', '+ Esf', '+ Plano' ou '+ Caps' no painel esquerdo para adicionar objetos à cena."),
    ("Templates prontos",
     "Clique em 'Templates' para carregar uma cena pronta: Plataformer, Arremesso ou Sandbox."),
    ("Propriedades do objeto",
     "Clique num objeto para selecioná-lo. No painel direito você ajusta posição, tamanho, cor, física e scripts."),
    ("Renomear objetos",
     "Dê dois cliques no nome do objeto na lista (painel esquerdo) ou pressione F2 para renomeá-lo."),
    ("Scripts prontos",
     "No inspetor, use '< >' para escolher um script pronto. Ex: builtin_wasd.py move o objeto com WASD."),
    ("Tags para colisões",
     "Defina a 'Tag' do objeto (ex: player, inimigo). Scripts podem detectar colisões pela tag."),
    ("Modo de câmera",
     "Use o botão 'Câmera' no topo para trocar entre Perspectiva, Top-Down e Side-Scroller."),
    ("Testar o jogo",
     "Clique em PLAY para testar. Clique em STOP para voltar ao editor. Posições são restauradas."),
]

SNAP_SIZE: float = 0.5

_SHAPE_ICON = {
    "Cube":    "▣",
    "Pyramid": "△",
    "Sphere":  "●",
    "Plane":   "▬",
    "Capsule": "⬬",
}


class EditorScene(Scene):

    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []
        self.editable_objects: List[GameObject] = []
        self.selected_index: int = -1

        self.font_title = self.font_body = self.font_btn = self.font_xyz = None

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

        self.cube_count = self.pyramid_count = self.sphere_count = 0
        self.plane_count = self.capsule_count = 0
        self.history = History()
        self.snap_enabled: bool = False

        self._tag_index: int = 0

        # Tree/outliner state
        self._tree_scroll: int = 0
        self._rename_index: int = -1
        self._rename_text: str = ""
        self._rename_blink: float = 0.0
        self._rename_cursor_on: bool = True
        self._last_click_index: int = -1
        self._last_click_time: float = 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # start
    # ──────────────────────────────────────────────────────────────────────────
    def start(self) -> None:
        print("[EditorScene] Iniciando editor 3D...")
        self.font_title = Assets.get_font(None, 18)
        self.font_body  = Assets.get_font(None, 15)
        self.font_btn   = Assets.get_font(None, 14)
        self.font_xyz   = Assets.get_font(None, 16)

        self.available_scripts = ScriptManager.list_scripts()

        # ── Painel esquerdo ── formas (linha 1 e 2) ──────────────────────────
        _BX = 15
        self.btn_add_cube    = GuiButton(_BX,      50, 56, 28, "+ Cubo",   bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_pyramid = GuiButton(_BX+60,   50, 56, 28, "+ Pirâm",  bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_sphere  = GuiButton(_BX+120,  50, 56, 28, "+ Esfera", bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_add_plane   = GuiButton(_BX,      82, 84, 28, "+ Plano",  bg_color=(40,80,100),  hover_color=(50,105,130))
        self.btn_add_capsule = GuiButton(_BX+90,   82, 84, 28, "+ Cápsula",bg_color=(40,80,100),  hover_color=(50,105,130))

        # ── Painel esquerdo ── modos de gizmo ───────────────────────────────
        self.btn_mode_translate = GuiButton(_BX,      115, 74, 26, "Mover",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_rotate    = GuiButton(_BX+78,   115, 74, 26, "Girar",   bg_color=(80,60,120),  hover_color=(100,80,150))
        self.btn_mode_scale     = GuiButton(_BX+156,  115, 74, 26, "Escalar", bg_color=(80,60,120),  hover_color=(100,80,150))

        # ── Painel esquerdo ── snap + templates ──────────────────────────────
        self.btn_snap      = GuiButton(_BX, 147, 230, 24, "Grade: OFF",     bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_templates = GuiButton(_BX, 175, 230, 24, "📂 Templates",   bg_color=(60,40,100), hover_color=(80,55,130))

        # ── Painel esquerdo ── tree ──────────────────────────────────────────
        _TREE_INNER_W = 196   # largura da caixa da lista
        self.btn_tree_up   = GuiButton(_LEFT_W - 38, _TREE_Y,              30, 20, "▲", bg_color=(55,58,68), hover_color=(70,75,88))
        self.btn_tree_down = GuiButton(_LEFT_W - 38, _TREE_Y + _TREE_H - 20, 30, 20, "▼", bg_color=(55,58,68), hover_color=(70,75,88))

        # ── Painel esquerdo ── undo/redo/delete ──────────────────────────────
        _CTRL_Y = _TREE_Y + _TREE_H + 18
        self.btn_undo   = GuiButton(_BX,      _CTRL_Y,      110, 28, "↩ Desfazer",    bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_redo   = GuiButton(_BX+115,  _CTRL_Y,      110, 28, "Refazer ↪",     bg_color=(60,65,78),  hover_color=(80,88,105))
        self.btn_delete = GuiButton(_BX,      _CTRL_Y + 34, 230, 28, "Excluir Objeto", bg_color=(140,40,40), hover_color=(175,50,50))

        # ── Painel esquerdo ── luz ───────────────────────────────────────────
        _LIGHT_Y = _CTRL_Y + 80
        self.btn_light_angle_dec = GuiButton(_BX,        _LIGHT_Y, 44, 24, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_light_angle_inc = GuiButton(_BX + 186,  _LIGHT_Y, 44, 24, " > ", bg_color=(60,65,78), hover_color=(75,80,95))
        self._light_y = _LIGHT_Y

        # ── Barra de topo ────────────────────────────────────────────────────
        self.btn_play_pause  = GuiButton(_VP_X + 10,  10, 90,  30, "PLAY",           bg_color=(40,120,60),  hover_color=(50,150,80))
        self.btn_save        = GuiButton(_VP_X + 110, 10, 80,  30, "Salvar",         bg_color=(100,70,40),  hover_color=(130,90,50))
        self.btn_load        = GuiButton(_VP_X + 200, 10, 80,  30, "Carregar",       bg_color=(100,70,40),  hover_color=(130,90,50))
        self.btn_camera_mode = GuiButton(_VP_X + 290, 10, 120, 30, "Câmera: Persp",  bg_color=(40,70,120),  hover_color=(55,95,160))
        self.btn_welcome     = GuiButton(_VP_X + 420, 10, 70,  30, "❓ Ajuda",        bg_color=(80,60,20),   hover_color=(110,85,30))

        # ── Painel direito ── posição base ───────────────────────────────────
        _RX = _RIGHT_X + 12   # margem interna
        _RW = _RIGHT_W - 24   # largura útil (244px)

        self.btn_toggle_static  = GuiButton(_RX,       60,  22, 22, "", bg_color=(45,49,58), hover_color=(70,76,90))
        self.btn_toggle_physics = GuiButton(_RX,       90,  22, 22, "", bg_color=(45,49,58), hover_color=(70,76,90))

        self.btn_vel_dec = GuiButton(_RX,        148, 44, 22, " - ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_vel_inc = GuiButton(_RX + _RW - 44, 148, 44, 22, " + ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_prev_script     = GuiButton(_RX,              198, 32, 24, " < ", bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_next_script     = GuiButton(_RX + _RW - 32,   198, 32, 24, " > ", bg_color=(60,65,78),  hover_color=(75,80,95))
        self.btn_new_script      = GuiButton(_RX,              226, _RW, 22, "+ Novo Script",     bg_color=(40,100,60),  hover_color=(50,130,80))
        self.btn_edit_script     = GuiButton(_RX,              252, _RW//2 - 2, 22, "Editor Ext.",  bg_color=(0,100,160),  hover_color=(0,130,200))
        self.btn_internal_editor = GuiButton(_RX + _RW//2 + 2, 252, _RW//2 - 2, 22, "Editor Int.", bg_color=(0,100,160),  hover_color=(0,130,200))
        self.btn_script_help     = GuiButton(_RX,              278, _RW, 22, "Guia de Comandos",  bg_color=(120,80,40),  hover_color=(150,100,50))

        self.btn_clone  = GuiButton(_RX, 360, _RW, 28, "Clonar Objeto", bg_color=(80,60,120), hover_color=(100,75,150))

        self.btn_prev_tag = GuiButton(_RX,             394, 32, 24, " < ", bg_color=(60,65,78), hover_color=(75,80,95))
        self.btn_next_tag = GuiButton(_RX + _RW - 32,  394, 32, 24, " > ", bg_color=(60,65,78), hover_color=(75,80,95))

        self.btn_colors = [
            GuiButton(_RX + i * (_RW // 6), 320, _RW // 6 - 2, 28, "", bg_color=c, hover_color=c)
            for i, c in enumerate(COLOR_PALETTE)
        ]

        # ── Templates modal ──────────────────────────────────────────────────
        self.showing_templates = False
        self._template_list    = self._load_template_list()
        self.btn_template_items = []
        for i, tpl in enumerate(self._template_list):
            self.btn_template_items.append(
                GuiButton(350, 130 + i * 62, 500, 50,
                          tpl.get("_template_name", f"Template {i+1}"),
                          bg_color=(50,55,70), hover_color=(70,78,100))
            )
        self.btn_templates_close = GuiButton(800, 90, 80, 28, "Fechar", bg_color=(140,40,40), hover_color=(175,50,50))

        # ── Câmera ───────────────────────────────────────────────────────────
        cam_obj = GameObject("EditorCamera")
        self.camera_comp = cam_obj.add_component(Camera3D(
            fov=60.0, near=0.1, far=100.0,
            viewport_x=float(_VP_X),
            viewport_y=float(_VP_Y),
            viewport_width=float(_VP_W),
            viewport_height=float(_VP_H),
        ))
        self.camera_controller = cam_obj.add_component(OrbitCameraController())
        self._add_go(cam_obj)

        self.spawn_object("Cube")

    # ──────────────────────────────────────────────────────────────────────────
    # helpers internos
    # ──────────────────────────────────────────────────────────────────────────
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
        self._tree_scroll = 0
        self._cancel_rename()
        self.cube_count = self.pyramid_count = self.sphere_count = 0
        self.plane_count = self.capsule_count = 0
        for item in tpl.get("objects", []):
            go = self._deserialize_object(item)
            self._add_go(go)
            self.editable_objects.append(go)
        if self.editable_objects:
            self.selected_index = 0
        self.showing_templates = False
        print(f"[EditorScene] Template carregado: {tpl.get('_template_name')}")

    def _set_camera_mode(self, mode_name: str) -> None:
        preset = CAMERA_MODE_PRESETS.get(mode_name, CAMERA_MODE_PRESETS["Perspectiva"])
        self.camera_controller.target_yaw      = preset["yaw"]
        self.camera_controller.target_pitch    = preset["pitch"]
        self.camera_controller.target_distance = preset["dist"]
        self.btn_camera_mode.text = f"Câmera: {mode_name[:5]}"

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

    def _make_mesh(self, shape: str, color: tuple):
        if shape == "Cube":
            return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)
        elif shape == "Pyramid":
            return MeshRenderer3D(create_pyramid_mesh(1.0), color=color)
        elif shape == "Sphere":
            return MeshRenderer3D(create_sphere_mesh(radius=0.6, rings=10, sectors=10), color=color)
        elif shape == "Plane":
            return MeshRenderer3D(create_plane_mesh(size=2.0, subdivisions=2), color=color)
        elif shape == "Capsule":
            return MeshRenderer3D(create_capsule_mesh(radius=0.4, height=1.0, rings=8, sectors=10), color=color)
        else:
            return MeshRenderer3D(Assets.create_cube_mesh(1.0), color=color)

    def _deserialize_object(self, item: Dict) -> GameObject:
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
        color = tuple(item["color"])
        go.add_component(self._make_mesh(go.mesh_type, color))
        if go.mesh_type == "Cube":     self.cube_count    += 1
        elif go.mesh_type == "Pyramid": self.pyramid_count += 1
        elif go.mesh_type == "Sphere":  self.sphere_count  += 1
        elif go.mesh_type == "Plane":   self.plane_count   += 1
        elif go.mesh_type == "Capsule": self.capsule_count += 1
        return go

    def _serialize_object(self, obj: GameObject) -> Dict[str, Any]:
        r = obj.get_component(MeshRenderer3D)
        return {
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
        }

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
            "Cube":    (0, 110, 220), "Pyramid": (220, 60, 20),
            "Sphere":  (100, 40, 180), "Plane":  (60, 160, 80),
            "Capsule": (200, 140, 0),
        }
        default_names = {
            "Cube": "Bloco", "Pyramid": "Piramide", "Sphere": "Bolinha",
            "Plane": "Plano", "Capsule": "Capsula",
        }
        count_map = {
            "Cube": "cube_count", "Pyramid": "pyramid_count", "Sphere": "sphere_count",
            "Plane": "plane_count", "Capsule": "capsule_count",
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

    def delete_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self._cancel_rename()
        self.history.push(self)
        go = self.editable_objects.pop(self.selected_index)
        self._remove_go(go)
        go.destroy()
        self.selected_index = -1 if not self.editable_objects else max(0, self.selected_index - 1)
        self._tree_scroll_to(self.selected_index)

    def clone_selected(self) -> None:
        if not (0 <= self.selected_index < len(self.editable_objects)):
            return
        self.history.push(self)
        src = self.editable_objects[self.selected_index]
        go  = GameObject()
        go.mesh_type          = getattr(src, "mesh_type", "Cube")
        go.name               = src.name + "_Clone"
        go.is_static          = getattr(src, "is_static", False)
        go.use_physics        = getattr(src, "use_physics", True)
        go.initial_velocity_y = getattr(src, "initial_velocity_y", 0.0)
        go.script_path        = getattr(src, "script_path", "")
        go.tag                = getattr(src, "tag", "")
        go.transform.position = src.transform.position + np.array([0.5, 0.0, 0.5], np.float32)
        go.transform.rotation = src.transform.rotation.copy()
        go.transform.scale    = src.transform.scale.copy()
        renderer = src.get_component(MeshRenderer3D)
        color    = renderer.color if renderer else (200, 200, 200)
        go.add_component(self._make_mesh(go.mesh_type, color))
        self._add_go(go)
        self.editable_objects.append(go)
        self.selected_index = len(self.editable_objects) - 1
        self._tree_scroll_to(self.selected_index)

    def _start_rename(self, idx: int) -> None:
        if not (0 <= idx < len(self.editable_objects)):
            return
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
        if idx < 0:
            return
        if idx < self._tree_scroll:
            self._tree_scroll = idx
        elif idx >= self._tree_scroll + _TREE_MAX_VIS:
            self._tree_scroll = idx - _TREE_MAX_VIS + 1

    def _max_scroll(self) -> int:
        return max(0, len(self.editable_objects) - _TREE_MAX_VIS)

    # ──────────────────────────────────────────────────────────────────────────
    # save / load
    # ──────────────────────────────────────────────────────────────────────────
    def save_scene(self) -> None:
        data = {"objects": [self._serialize_object(o) for o in self.editable_objects]}
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            print("[EditorScene] Cena salva.")
        except Exception as e:
            print(f"[EditorScene] Erro ao salvar: {e}")

    def load_scene(self) -> None:
        path = os.path.join(os.path.dirname(__file__), "..", "demos", "scene.json")
        if not os.path.exists(path):
            print("[EditorScene] Nenhuma cena salva."); return
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[EditorScene] Erro: {e}"); return
        self.history.push(self)
        for obj in list(self.editable_objects):
            self._remove_go(obj); obj.destroy()
        self.editable_objects.clear()
        self.selected_index = -1
        self._tree_scroll = 0
        self._cancel_rename()
        self.cube_count = self.pyramid_count = self.sphere_count = 0
        self.plane_count = self.capsule_count = 0
        for item in data.get("objects", []):
            go = self._deserialize_object(item)
            self._add_go(go)
            self.editable_objects.append(go)
        if self.editable_objects:
            self.selected_index = len(self.editable_objects) - 1
        print("[EditorScene] Cena carregada.")

    # ──────────────────────────────────────────────────────────────────────────
    # play / stop
    # ──────────────────────────────────────────────────────────────────────────
    def _toggle_play(self) -> None:
        self.play_mode = not self.play_mode
        if self.play_mode:
            self.saved_scene_state = [self._serialize_object(o) for o in self.editable_objects]
            for obj in self.editable_objects:
                ScriptManager.load(obj)
        else:
            for obj in self.editable_objects:
                ScriptManager.unload(obj)
            if self.saved_scene_state is not None:
                for obj in list(self.editable_objects):
                    self._remove_go(obj)
                    obj.destroy()
                self.editable_objects.clear()
                self.cube_count = self.pyramid_count = self.sphere_count = 0
                self.plane_count = self.capsule_count = 0
                for item in self.saved_scene_state:
                    go = self._deserialize_object(item)
                    self._add_go(go)
                    self.editable_objects.append(go)
                self.selected_index = min(self.selected_index, len(self.editable_objects) - 1)
                self._tree_scroll_to(self.selected_index)

    # ──────────────────────────────────────────────────────────────────────────
    # seleção por clique no viewport
    # ──────────────────────────────────────────────────────────────────────────
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
            self._tree_scroll_to(self.selected_index)

    # ──────────────────────────────────────────────────────────────────────────
    # update
    # ──────────────────────────────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        if self._rename_index >= 0:
            self._rename_blink += dt
            if self._rename_blink >= 0.5:
                self._rename_blink = 0.0
                self._rename_cursor_on = not self._rename_cursor_on

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
                if   self.active_gizmo_axis == 'x': sel.transform.scale[0] = max(0.1, sel.transform.scale[0]+dx*0.015)
                elif self.active_gizmo_axis == 'y': sel.transform.scale[1] = max(0.1, sel.transform.scale[1]-dy*0.015)
                elif self.active_gizmo_axis == 'z': sel.transform.scale[2] = max(0.1, sel.transform.scale[2]-dy*0.015)
                elif self.active_gizmo_axis == 'center':
                    ns = max(0.1, sel.transform.scale[0]+(dx-dy)*0.015)
                    sel.transform.scale = np.array([ns,ns,ns], np.float32)
            elif self.gizmo_mode == "rotate":
                if   self.active_gizmo_axis == 'x': sel.transform.rotation[0] = (sel.transform.rotation[0]+dy*0.5)%360
                elif self.active_gizmo_axis == 'y': sel.transform.rotation[1] = (sel.transform.rotation[1]+dx*0.5)%360
                elif self.active_gizmo_axis == 'z': sel.transform.rotation[2] = (sel.transform.rotation[2]+dx*0.5)%360
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
                yr  = np.radians(self.camera_controller.yaw)
                pr  = np.radians(self.camera_controller.pitch)
                right = np.array([np.cos(yr), 0.0, -np.sin(yr)], np.float32)
                up    = np.array([np.sin(pr)*np.sin(yr), np.cos(pr), np.sin(pr)*np.cos(yr)], np.float32)
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

    # ──────────────────────────────────────────────────────────────────────────
    # draw
    # ──────────────────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface) -> None:
        # fundo geral
        screen.fill((28, 30, 36))
        # viewport
        pygame.draw.rect(screen, (255,255,255), (_VP_X, _VP_Y, _VP_W, _VP_H))
        self._draw_floor_grid(screen)
        for go in self.game_objects:
            go.draw(screen)
            if self.selected_index >= 0 and go == self.editable_objects[self.selected_index]:
                r = go.get_component(MeshRenderer3D)
                if r:
                    ow,oc,olw = r.wireframe, r.color, r.line_width
                    r.wireframe, r.color, r.line_width = True, (255,0,0), 3
                    r.draw(screen)
                    r.wireframe, r.color, r.line_width = ow, oc, olw
        self._draw_gizmo(screen)
        self._draw_top_bar(screen)
        self._draw_left_panel(screen)
        self._draw_right_panel(screen)
        self._draw_xyz_widget(screen)
        if self.showing_templates:
            self._draw_templates_modal(screen)
        elif self.code_editor.is_open:
            self.code_editor.draw(screen)
        elif self.showing_help_modal:
            self._draw_help_modal(screen)
        elif self.showing_welcome:
            self._draw_welcome_modal(screen)

    def _draw_floor_grid(self, screen: pygame.Surface) -> None:
        verts = []
        for x in range(-5, 6): verts += [[x,-0.5,-5.0],[x,-0.5,5.0]]
        for z in range(-5, 6): verts += [[-5.0,-0.5,z],[5.0,-0.5,z]]
        verts = np.array(verts, np.float32)
        ndc, depths = project_vertices(verts, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x,    self.camera_comp.viewport_y
        sx = vx + (ndc[:,0]+1)*vw/2
        sy = vy + (-ndc[:,1]+1)*vh/2
        near = self.camera_comp.near
        for i in range(0, len(verts), 2):
            if depths[i] > near and depths[i+1] > near:
                p0 = (int(sx[i]),   int(sy[i]))
                p1 = (int(sx[i+1]), int(sy[i+1]))
                center = (
                    (abs(verts[i][0])<0.01 and abs(verts[i][2]-verts[i+1][2])>0.01) or
                    (abs(verts[i][2])<0.01 and abs(verts[i][0]-verts[i+1][0])>0.01)
                )
                pygame.draw.line(screen, (170,175,185) if center else (220,222,226), p0, p1, 2 if center else 1)

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
        if not all(d > near for d in depths):
            return
        vw, vh = self.camera_comp.viewport_width, self.camera_comp.viewport_height
        vx, vy = self.camera_comp.viewport_x,    self.camera_comp.viewport_y
        def ts(i): return int(vx+(ndc[i,0]+1)*vw/2), int(vy+(-ndc[i,1]+1)*vh/2)
        c, px, py, pz = ts(0), ts(1), ts(2), ts(3)
        self.gizmo_screen_points = {'x': px, 'y': py, 'z': pz}
        self.gizmo_screen_center = c
        if self.gizmo_mode == "rotate":
            for pts_fn, col in [
                (lambda t: P+np.array([0.8*np.cos(t),0,0.8*np.sin(t)],np.float32), (50,170,50)),
                (lambda t: P+np.array([0,0.8*np.cos(t),0.8*np.sin(t)],np.float32), (220,50,50)),
                (lambda t: P+np.array([0.8*np.cos(t),0.8*np.sin(t),0],np.float32), (50,100,220)),
            ]:
                ring = np.array([pts_fn(t) for t in np.linspace(0,2*np.pi,20)], np.float32)
                rn, rd = project_vertices(ring, _IDENTITY, self.camera_comp.view_matrix, self.camera_comp.projection_matrix)
                pts = [(int(vx+(rn[k,0]+1)*vw/2), int(vy+(-rn[k,1]+1)*vh/2)) for k in range(len(ring)) if rd[k]>near]
                if len(pts) > 1:
                    pygame.draw.lines(screen, col, True, pts, 1)
        else:
            pygame.draw.line(screen,(220,50,50), c,px,3)
            pygame.draw.line(screen,(50,170,50), c,py,3)
            pygame.draw.line(screen,(50,100,220),c,pz,3)
            if self.gizmo_mode == "translate":
                for pt,col in [(px,(220,50,50)),(py,(50,170,50)),(pz,(50,100,220))]:
                    pygame.draw.circle(screen,col,pt,7)
            elif self.gizmo_mode == "scale":
                for pt,col in [(px,(220,50,50)),(py,(50,170,50)),(pz,(50,100,220))]:
                    pygame.draw.rect(screen,col,(pt[0]-6,pt[1]-6,12,12))
                pygame.draw.circle(screen,(240,200,0),c,6)

    def _draw_top_bar(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (30,33,40), (0, 0, WIN_W, _TOP_H))
        pygame.draw.line(screen, (55,60,72), (0, _TOP_H), (WIN_W, _TOP_H), 1)
        # logo
        screen.blit(self.font_title.render("Zennity Engine", True, (0,200,255)), (10, 14))
        # botões
        self.btn_play_pause.bg_color    = (180,40,40) if self.play_mode else (40,120,60)
        self.btn_play_pause.hover_color = (220,50,50) if self.play_mode else (50,150,80)
        self.btn_play_pause.text        = "STOP" if self.play_mode else "PLAY"
        for btn in [self.btn_play_pause, self.btn_save, self.btn_load, self.btn_camera_mode, self.btn_welcome]:
            btn.draw(screen, self.font_btn)
        undo_col = (0,200,255) if self.history.can_undo else (80,85,95)
        redo_col = (0,200,255) if self.history.can_redo else (80,85,95)
        screen.blit(self.font_btn.render(f"↩{len(self.history._undo)}",True,undo_col), (_VP_X+500, 16))
        screen.blit(self.font_btn.render(f"{len(self.history._redo)}↪",True,redo_col), (_VP_X+540, 16))

    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (38,42,50), (0, 0, _LEFT_W, WIN_H))
        pygame.draw.line(screen, (55,60,72), (_LEFT_W,0), (_LEFT_W, WIN_H), 2)

        screen.blit(self.font_title.render("ADICIONAR FORMAS", True, (0,200,255)), (15, 24))
        for btn in [self.btn_add_cube, self.btn_add_pyramid, self.btn_add_sphere,
                    self.btn_add_plane, self.btn_add_capsule]:
            btn.draw(screen, self.font_btn)

        for btn, mode in [
            (self.btn_mode_translate,"translate"),
            (self.btn_mode_rotate,"rotate"),
            (self.btn_mode_scale,"scale")
        ]:
            btn.bg_color = (0,150,220) if self.gizmo_mode == mode else (80,60,120)
            btn.draw(screen, self.font_btn)

        self.btn_snap.text     = f"Grade: {'ON (G)' if self.snap_enabled else 'OFF (G)'}"
        self.btn_snap.bg_color = (0,130,80) if self.snap_enabled else (55,58,68)
        self.btn_snap.draw(screen, self.font_btn)
        self.btn_templates.draw(screen, self.font_btn)

        # ── tree ──
        screen.blit(self.font_title.render("OBJETOS DA CENA", True, (0,200,255)), (15, _TREE_LABEL_Y))
        pygame.draw.rect(screen, (30,34,42),  (15, _TREE_Y, 210, _TREE_H), border_radius=3)
        pygame.draw.rect(screen, (55,60,72),  (15, _TREE_Y, 210, _TREE_H), 1, border_radius=3)

        total = len(self.editable_objects)
        max_s = self._max_scroll()
        self._tree_scroll = min(self._tree_scroll, max_s)

        for slot_i in range(_TREE_MAX_VIS):
            obj_i = self._tree_scroll + slot_i
            if obj_i >= total:
                break
            obj = self.editable_objects[obj_i]
            sel = (obj_i == self.selected_index)
            ry  = _TREE_Y + slot_i * _TREE_ROW_H
            row = pygame.Rect(16, ry, 208, _TREE_ROW_H - 1)

            pygame.draw.rect(screen, (60,80,110) if sel else (38,42,50), row, border_radius=2)
            if sel:
                pygame.draw.rect(screen, (0,200,255), row, 1, border_radius=2)

            icon = _SHAPE_ICON.get(getattr(obj, "mesh_type", "Cube"), "■")
            screen.blit(self.font_body.render(icon, True, (0,200,255) if sel else (120,130,145)), (22, ry+3))

            if self._rename_index == obj_i:
                pygame.draw.rect(screen, (50,55,65),  (40, ry+2, 176, _TREE_ROW_H-4), border_radius=2)
                pygame.draw.rect(screen, (0,200,255), (40, ry+2, 176, _TREE_ROW_H-4), 1, border_radius=2)
                display = self._rename_text + ("|" if self._rename_cursor_on else "")
                screen.blit(self.font_body.render(display, True, (255,255,255)), (43, ry+3))
            else:
                label = obj.name
                if len(label) > 18:
                    label = label[:16] + ".."
                screen.blit(self.font_body.render(label, True, (255,255,255)), (40, ry+3))

        if total > _TREE_MAX_VIS:
            bar_h = max(16, _TREE_H * _TREE_MAX_VIS // max(total, 1))
            bar_y = _TREE_Y + (_TREE_H - bar_h) * self._tree_scroll // max(max_s, 1)
            pygame.draw.rect(screen, (80,88,105), (226, bar_y, 4, bar_h), border_radius=2)
            self.btn_tree_up.draw(screen, self.font_btn)
            self.btn_tree_down.draw(screen, self.font_btn)

        screen.blit(self.font_body.render(f"{total} objeto(s)", True, (100,105,115)), (15, _TREE_Y + _TREE_H + 4))

        # undo/redo/delete
        self.btn_undo.bg_color = (60,80,110) if self.history.can_undo else (45,49,58)
        self.btn_redo.bg_color = (60,80,110) if self.history.can_redo else (45,49,58)
        self.btn_undo.draw(screen, self.font_btn)
        self.btn_redo.draw(screen, self.font_btn)
        if 0 <= self.selected_index < len(self.editable_objects):
            self.btn_delete.draw(screen, self.font_btn)

        # luz
        screen.blit(self.font_title.render("DIREÇÃO DA LUZ", True, (0,200,255)), (15, self._light_y - 22))
        self.btn_light_angle_dec.draw(screen, self.font_btn)
        screen.blit(self.font_body.render(f"Sol: {int(self.light_angle)}°", True, (255,255,255)), (70, self._light_y + 2))
        self.btn_light_angle_inc.draw(screen, self.font_btn)

    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(screen, (38,42,50), (_RIGHT_X, 0, _RIGHT_W, WIN_H))
        pygame.draw.line(screen, (55,60,72), (_RIGHT_X, 0), (_RIGHT_X, WIN_H), 2)

        _RX = _RIGHT_X + 12
        _RW = _RIGHT_W - 24

        if not (0 <= self.selected_index < len(self.editable_objects)):
            screen.blit(self.font_body.render("Selecione um objeto", True, (140,145,155)), (_RX, 60))
            return

        sel = self.editable_objects[self.selected_index]
        pos, rot, sc = sel.transform.position, sel.transform.rotation, sel.transform.scale

        y = 18
        screen.blit(self.font_title.render("PROPRIEDADES 3D", True, (0,200,255)), (_RX, y)); y += 30

        # estático
        self.btn_toggle_static.draw(screen, self.font_btn)
        if getattr(sel, "is_static", False):
            pygame.draw.rect(screen, (0,200,255), (_RX+4, 64, 14, 14))
        screen.blit(self.font_body.render("Estático", True, (240,240,240)), (_RX+28, 62))

        # física
        self.btn_toggle_physics.draw(screen, self.font_btn)
        if getattr(sel, "use_physics", True):
            pygame.draw.rect(screen, (0,200,255), (_RX+4, 94, 14, 14))
        screen.blit(self.font_body.render("Simular Gravidade", True, (240,240,240)), (_RX+28, 92))

        # impulso
        screen.blit(self.font_body.render("Impulso Vertical:", True, (220,220,220)), (_RX, 126))
        self.btn_vel_dec.draw(screen, self.font_btn)
        iv = getattr(sel, "initial_velocity_y", 0.0)
        screen.blit(self.font_body.render(f"{iv:+.1f} m/s", True, (255,255,255)), (_RX + _RW//2 - 20, 150))
        self.btn_vel_inc.draw(screen, self.font_btn)

        # script
        screen.blit(self.font_body.render("Script:", True, (220,220,220)), (_RX, 180))
        self.btn_prev_script.draw(screen, self.font_btn)
        pygame.draw.rect(screen, (45,49,58), (_RX+36, 198, _RW-72, 24), border_radius=3)
        sn = os.path.basename(getattr(sel, "script_path", "")) or "Nenhum"
        if len(sn) > 16: sn = sn[:14] + ".."
        screen.blit(self.font_body.render(sn, True, (255,255,255)), (_RX+40, 202))
        self.btn_next_script.draw(screen, self.font_btn)
        for btn in [self.btn_new_script, self.btn_edit_script, self.btn_internal_editor, self.btn_script_help]:
            btn.draw(screen, self.font_btn)

        # cor
        screen.blit(self.font_body.render("Cor do Objeto:", True, (220,220,220)), (_RX, 306))
        for btn in self.btn_colors:
            btn.draw(screen, self.font_btn)

        # clonar
        self.btn_clone.draw(screen, self.font_btn)

        # tag
        screen.blit(self.font_body.render("Tag:", True, (220,220,220)), (_RX, 380))
        self.btn_prev_tag.draw(screen, self.font_btn)
        tag_val = getattr(sel, "tag", "") or "Nenhuma"
        pygame.draw.rect(screen, (45,49,58), (_RX+36, 394, _RW-72, 24), border_radius=3)
        screen.blit(self.font_body.render(tag_val, True, (255,255,255)), (_RX+40, 398))
        self.btn_next_tag.draw(screen, self.font_btn)

        # barra de status na base do painel
        snap_tag = " [SNAP]" if self.snap_enabled else ""
        sy_bar = WIN_H - 50
        pygame.draw.rect(screen, (30,34,42), (_RIGHT_X, sy_bar, _RIGHT_W, 50))
        pygame.draw.line(screen, (0,200,255), (_RIGHT_X, sy_bar), (_RIGHT_X + _RIGHT_W, sy_bar), 1)
        name_trunc = sel.name[:22]
        screen.blit(self.font_xyz.render(f"{name_trunc}{snap_tag}", True, (0,200,255)), (_RX, sy_bar + 6))
        screen.blit(self.font_body.render(
            f"P {pos[0]:.1f} {pos[1]:.1f} {pos[2]:.1f}",
            True, (200,200,200)), (_RX, sy_bar + 24))
        screen.blit(self.font_body.render(
            f"S {sc[0]:.1f} {sc[1]:.1f} {sc[2]:.1f}  R {int(rot[1])}°",
            True, (200,200,200)), (_RX, sy_bar + 38))

    def _draw_xyz_widget(self, screen: pygame.Surface) -> None:
        C  = (_RIGHT_X - 55, _VP_Y + 55)
        vr = self.camera_comp.view_matrix[:3,:3]
        ax = 38.0
        dirs = [
            (vr@np.array([0,0,-1],np.float32),"X",(220,50,50)),
            (vr@np.array([0,1, 0],np.float32),"Y",(50,170,50)),
            (vr@np.array([1,0, 0],np.float32),"Z",(50,100,220)),
        ]
        endpoints = []
        for d, label, col in dirs:
            e = (int(C[0]+ax*d[0]), int(C[1]-ax*d[1]))
            endpoints.append(np.array(e, np.float32))
            pygame.draw.line(screen, col, C, e, 2)
            pygame.draw.circle(screen, col, e, 9)
            lbl = self.font_xyz.render(label, True, (255,255,255))
            screen.blit(lbl, lbl.get_rect(center=e))
        pygame.draw.circle(screen, (120,125,135), C, 4)
        self.gizmo_ex, self.gizmo_ey, self.gizmo_ez = endpoints

    def _draw_help_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((20,24,30,230)); screen.blit(ov,(0,0))
        modal = pygame.Rect(150, 50, 900, 560)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=8)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=8)
        screen.blit(self.font_title.render("Guia de Comandos — Zennity Engine",True,(0,200,255)),(170,62))
        screen.blit(self.font_btn.render("[ESC] Fechar",True,(200,80,80)),(960,62))
        y = 110
        for line in HELP_LINES:
            col = (0,200,255) if line.startswith("  ") else (220,222,226)
            screen.blit(self.font_body.render(line,True,col),(190,y)); y += 18

    def _draw_templates_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((20,24,30,230)); screen.blit(ov,(0,0))
        modal = pygame.Rect(330, 70, 560, 100 + len(self._template_list)*62 + 40)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=8)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=8)
        screen.blit(self.font_title.render("Carregar Template",True,(0,200,255)),(355,85))
        self.btn_templates_close.draw(screen, self.font_btn)
        for i, (btn, tpl) in enumerate(zip(self.btn_template_items, self._template_list)):
            btn.draw(screen, self.font_btn)
            desc = tpl.get("_template_desc","")
            if desc:
                screen.blit(self.font_body.render(desc[:65],True,(160,165,175)),(355, 130+i*62+28))

    def _draw_welcome_modal(self, screen: pygame.Surface) -> None:
        ov = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        ov.fill((10,14,20,210)); screen.blit(ov,(0,0))
        modal = pygame.Rect(300, 200, 700, 240)
        pygame.draw.rect(screen,(30,34,42),modal,border_radius=10)
        pygame.draw.rect(screen,(0,200,255),modal,2,border_radius=10)
        step = WELCOME_STEPS[self.welcome_step]
        screen.blit(self.font_title.render(step[0], True,(0,200,255)),(320,218))
        words = step[1].split()
        line_buf, lines_out = [], []
        for w in words:
            test = " ".join(line_buf+[w])
            if self.font_body.size(test)[0] > 630:
                lines_out.append(" ".join(line_buf))
                line_buf = [w]
            else:
                line_buf.append(w)
        if line_buf: lines_out.append(" ".join(line_buf))
        for i, ln in enumerate(lines_out):
            screen.blit(self.font_body.render(ln,True,(220,222,226)),(320,248+i*22))
        total = len(WELCOME_STEPS)
        screen.blit(self.font_btn.render(f"{self.welcome_step+1}/{total}",True,(120,125,135)),(320,380))
        if self.welcome_step > 0:
            pygame.draw.rect(screen,(60,65,78),(490,380,90,28),border_radius=5)
            screen.blit(self.font_btn.render("◀ Anterior",True,(200,200,200)),(496,386))
        pygame.draw.rect(screen,(40,120,60),(590,380,90,28),border_radius=5)
        screen.blit(self.font_btn.render("Próximo ▶" if self.welcome_step<total-1 else "Começar!",True,(255,255,255)),(596,386))
        pygame.draw.rect(screen,(120,40,40),(960,205,36,22),border_radius=5)
        screen.blit(self.font_btn.render("✕",True,(255,255,255)),(968,208))

    # ──────────────────────────────────────────────────────────────────────────
    # handle_event
    # ──────────────────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event) -> None:
        # ── rename inline ──
        if self._rename_index >= 0:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._commit_rename(); return
                elif event.key == pygame.K_ESCAPE:
                    self._cancel_rename(); return
                elif event.key == pygame.K_BACKSPACE:
                    self._rename_text = self._rename_text[:-1]; return
                else:
                    ch = event.unicode
                    if ch and ch.isprintable():
                        self._rename_text += ch
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if not pygame.Rect(15, _TREE_Y, 210, _TREE_H).collidepoint(mx, my):
                    self._commit_rename()

        # ── welcome modal ──
        if self.showing_welcome:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                total = len(WELCOME_STEPS)
                if pygame.Rect(960,205,36,22).collidepoint(mx,my):
                    self.showing_welcome = False; return
                if self.welcome_step > 0 and pygame.Rect(490,380,90,28).collidepoint(mx,my):
                    self.welcome_step -= 1; return
                if pygame.Rect(590,380,90,28).collidepoint(mx,my):
                    if self.welcome_step < total-1:
                        self.welcome_step += 1
                    else:
                        self.showing_welcome = False
                    return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_welcome = False
            return

        # ── templates modal ──
        if self.showing_templates:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_templates_close.is_clicked(event):
                    self.showing_templates = False; return
                for btn, tpl in zip(self.btn_template_items, self._template_list):
                    if btn.is_clicked(event):
                        self._load_template(tpl); return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_templates = False
            return

        if self.code_editor.handle_event(event):
            return
        if self.showing_help_modal:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.showing_help_modal = False
            return

        # ── teclas globais ──
        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key == pygame.K_z and mods & pygame.KMOD_CTRL:
                if mods & pygame.KMOD_SHIFT: self.history.redo(self)
                else:                        self.history.undo(self)
                return
            if event.key == pygame.K_d and mods & pygame.KMOD_CTRL:
                self.clone_selected(); return
            if event.key == pygame.K_DELETE:
                self.delete_selected(); return
            if event.key == pygame.K_g:
                self.snap_enabled = not self.snap_enabled; return
            if event.key == pygame.K_F2:
                self._start_rename(self.selected_index); return

        # ── botões painel esquerdo ──
        if self.btn_add_cube.is_clicked(event):    self.spawn_object("Cube");    return
        if self.btn_add_pyramid.is_clicked(event): self.spawn_object("Pyramid"); return
        if self.btn_add_sphere.is_clicked(event):  self.spawn_object("Sphere");  return
        if self.btn_add_plane.is_clicked(event):   self.spawn_object("Plane");   return
        if self.btn_add_capsule.is_clicked(event): self.spawn_object("Capsule"); return

        for btn, mode in [
            (self.btn_mode_translate,"translate"),
            (self.btn_mode_rotate,"rotate"),
            (self.btn_mode_scale,"scale")
        ]:
            if btn.is_clicked(event):
                self.gizmo_mode = None if self.gizmo_mode == mode else mode; return

        if self.btn_snap.is_clicked(event):      self.snap_enabled = not self.snap_enabled; return
        if self.btn_templates.is_clicked(event): self.showing_templates = True; return

        if self.btn_camera_mode.is_clicked(event):
            self.camera_mode_index = (self.camera_mode_index + 1) % len(CAMERA_MODES)
            self._set_camera_mode(CAMERA_MODES[self.camera_mode_index]); return

        if self.btn_welcome.is_clicked(event):
            self.showing_welcome = True
            self.welcome_step    = 0; return

        if self.btn_undo.is_clicked(event): self.history.undo(self); return
        if self.btn_redo.is_clicked(event): self.history.redo(self); return

        if self.btn_play_pause.is_clicked(event): self._toggle_play(); return
        if self.btn_save.is_clicked(event):       self.save_scene();   return
        if self.btn_load.is_clicked(event):       self.load_scene();   return

        if self.btn_tree_up.is_clicked(event):
            self._tree_scroll = max(0, self._tree_scroll - 1); return
        if self.btn_tree_down.is_clicked(event):
            self._tree_scroll = min(self._max_scroll(), self._tree_scroll + 1); return

        if self.btn_light_angle_dec.is_clicked(event) or self.btn_light_angle_inc.is_clicked(event):
            d = -15.0 if self.btn_light_angle_dec.is_clicked(event) else 15.0
            self.light_angle = (self.light_angle + d) % 360
            rad = np.radians(self.light_angle)
            ld  = np.array([np.cos(rad), 1.0, np.sin(rad)], np.float32)
            ld /= np.linalg.norm(ld)
            for obj in self.editable_objects:
                r = obj.get_component(MeshRenderer3D)
                if r: r.light_dir = ld
            return

        # ── scroll ──
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if pygame.Rect(15, _TREE_Y, 210, _TREE_H).collidepoint(mx, my):
                self._tree_scroll = max(0, min(self._max_scroll(), self._tree_scroll - event.y))
                return
            self.camera_controller.target_distance = max(1.5, min(15.0, self.camera_controller.target_distance - event.y*0.3))
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4: self.camera_controller.target_distance = max(1.5,  self.camera_controller.target_distance - 0.3)
            if event.button == 5: self.camera_controller.target_distance = min(15.0, self.camera_controller.target_distance + 0.3)

        # ── clique no widget xyz ──
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for ep, yaw, pitch in [
                (self.gizmo_ex,  0.0,  0.0),
                (self.gizmo_ey,  0.0, 85.0),
                (self.gizmo_ez, 90.0,  0.0),
            ]:
                if ep is not None and np.linalg.norm(np.array([mx,my])-ep) < 12.0:
                    self.camera_controller.target_yaw   = yaw
                    self.camera_controller.target_pitch = pitch
                    return

        # ── gizmo drag ──
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.selected_index >= 0 and not self.play_mode and self.gizmo_mode and self.gizmo_screen_points:
                if self.gizmo_mode == "scale" and self.gizmo_screen_center:
                    if np.linalg.norm(np.array([mx,my]) - np.array(self.gizmo_screen_center)) < 10.0:
                        self.history.push(self)
                        self.is_dragging_gizmo = True; self.active_gizmo_axis = 'center'
                        self.gizmo_drag_last_mouse = event.pos; return
                for axis, pt in self.gizmo_screen_points.items():
                    if np.linalg.norm(np.array([mx,my]) - np.array(pt)) < 12.0:
                        self.history.push(self)
                        self.is_dragging_gizmo = True; self.active_gizmo_axis = axis
                        self.gizmo_drag_last_mouse = event.pos; return

        # ── clique no viewport / tree ──
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click_start_pos = event.pos
            mx, my = event.pos
            if _VP_X <= mx <= _RIGHT_X and 0 <= self.selected_index < len(self.editable_objects):
                r = self.editable_objects[self.selected_index].get_component(MeshRenderer3D)
                if r and r.last_screen_coords is not None:
                    for face in r.mesh.faces:
                        if _point_in_polygon(mx, my, [tuple(r.last_screen_coords[vi]) for vi in face]):
                            self.history.push(self)
                            self.is_dragging_object    = True
                            self.drag_object_last_mouse = event.pos
                            break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_object = False
            self.is_dragging_gizmo  = False
            self.active_gizmo_axis  = None
            if self.click_start_pos:
                dx = event.pos[0] - self.click_start_pos[0]
                dy = event.pos[1] - self.click_start_pos[1]
                if np.hypot(dx, dy) < 4.0:
                    mx, my = event.pos
                    if mx < _LEFT_W:
                        tree_rect = pygame.Rect(15, _TREE_Y, 210, _TREE_H)
                        if tree_rect.collidepoint(mx, my):
                            slot_i = (my - _TREE_Y) // _TREE_ROW_H
                            obj_i  = self._tree_scroll + slot_i
                            if 0 <= obj_i < len(self.editable_objects):
                                now = pygame.time.get_ticks() / 1000.0
                                if obj_i == self._last_click_index and (now - self._last_click_time) < 0.4:
                                    self._start_rename(obj_i)
                                else:
                                    self.selected_index = obj_i
                                self._last_click_index = obj_i
                                self._last_click_time  = now
                    elif mx <= _RIGHT_X:
                        self._select_at(mx, my)
                self.click_start_pos = None

        # ── painel direito — objeto selecionado ──
        if 0 <= self.selected_index < len(self.editable_objects):
            sel = self.editable_objects[self.selected_index]
            if self.btn_delete.is_clicked(event):         self.delete_selected(); return
            if self.btn_toggle_static.is_clicked(event):
                self.history.push(self); sel.is_static = not getattr(sel, "is_static", False); return
            if self.btn_toggle_physics.is_clicked(event):
                self.history.push(self); sel.use_physics = not getattr(sel, "use_physics", True); return
            if self.btn_vel_dec.is_clicked(event):
                self.history.push(self); sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) - 1.0; return
            if self.btn_vel_inc.is_clicked(event):
                self.history.push(self); sel.initial_velocity_y = getattr(sel, "initial_velocity_y", 0.0) + 1.0; return
            if self.btn_clone.is_clicked(event): self.clone_selected(); return
            if self.btn_prev_script.is_clicked(event) or self.btn_next_script.is_clicked(event):
                cur = getattr(sel, "script_path", "")
                idx = self.available_scripts.index(cur) if cur in self.available_scripts else 0
                ni  = (idx + (-1 if self.btn_prev_script.is_clicked(event) else 1)) % len(self.available_scripts)
                sel.script_path = self.available_scripts[ni] if ni > 0 else ""; return
            if self.btn_new_script.is_clicked(event):
                path = ScriptManager.create_template(sel)
                self.available_scripts = ScriptManager.list_scripts()
                sel.script_path = path; return
            if self.btn_edit_script.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p):
                    try: os.startfile(p)
                    except: import subprocess; subprocess.Popen(["notepad.exe", p])
                return
            if self.btn_internal_editor.is_clicked(event):
                p = getattr(sel, "script_path", "")
                if p and os.path.exists(p): self.code_editor.open(p)
                return
            if self.btn_script_help.is_clicked(event): self.showing_help_modal = True; return
            if self.btn_prev_tag.is_clicked(event) or self.btn_next_tag.is_clicked(event):
                cur_tag = getattr(sel, "tag", "")
                try:    ti = TAG_OPTIONS.index(cur_tag)
                except: ti = 0
                delta = -1 if self.btn_prev_tag.is_clicked(event) else 1
                ti = (ti + delta) % len(TAG_OPTIONS)
                sel.tag = TAG_OPTIONS[ti]; return
            for i, btn in enumerate(self.btn_colors):
                if btn.is_clicked(event):
                    self.history.push(self)
                    r = sel.get_component(MeshRenderer3D)
                    if r: r.color = COLOR_PALETTE[i]
                    return
